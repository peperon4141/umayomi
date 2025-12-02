"""メインのオーケストレーター - シンプルで明確なデータ処理フロー"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd

from ._07_cache_manager import CacheManager
from ._06_column_selector import ColumnSelector
from ._02_jrdb_combiner import JrdbCombiner
from ._04_key_converter import KeyConverter
from ._01_parquet_loader import ParquetLoader
from ._05_time_series_splitter import TimeSeriesSplitter
from ._03_feature_extractor import FeatureExtractor


class DataProcessor:
    """データ処理のメインオーケストレーター"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None, use_cache: bool = True):
        """
        初期化
        
        Args:
            base_path: プロジェクトのベースパス（デフォルト: プロジェクトルート）
            use_cache: キャッシュを使用するかどうか（デフォルト: True）
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self._base_path = Path(base_path)

        self._parquet_loader = ParquetLoader(self._base_path / "apps" / "prediction" / "cache" / "jrdb" / "parquet")
        self._jrdb_combiner = JrdbCombiner(self._base_path)
        self._feature_extractor = FeatureExtractor()
        self._key_converter = KeyConverter(self._base_path)
        self._time_series_splitter = TimeSeriesSplitter()
        self._column_selector = ColumnSelector(self._base_path)
        
        # キャッシュマネージャーを初期化
        cache_dir = self._base_path / "apps" / "prediction" / "cache"
        self._cache_manager = CacheManager(cache_dir) if use_cache else None
        self._use_cache = use_cache

    def process(
        self,
        data_types: List[str],
        year: int = 2024,
        split_date: Optional[Union[str, datetime]] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        データ処理の全ステップを実行
        
        Args:
            data_types: データタイプのリスト
            year: 年度
            split_date: 時系列分割日時（指定時は分割実行）
        
        Returns:
            split_date指定時: (train_df, test_df, eval_df)
            split_date未指定時: converted_df
        """
        # キャッシュから読み込みを試行
        if self._use_cache and self._cache_manager is not None:
            cached_data = self._cache_manager.load(data_types, year, split_date)
            if cached_data is not None:
                print("キャッシュから前処理済みデータを読み込みました")
                return cached_data

        # ステップ1: データ読み込みと結合
        print("[_01_] データ読み込みと前処理を開始します...")
        data_dict = self._parquet_loader.load(data_types, year)
        print(f"[_01_] データ読み込み完了: {len(data_dict)}件のデータタイプ")
        
        print("[_02_] データ結合中...")
        raw_df = self._jrdb_combiner.combine(data_dict)
        print(f"[_02_] データ結合完了: {len(raw_df):,}件")

        # ステップ2: 特徴量追加（並列処理）
        bac_df = data_dict.get("BAC")
        if bac_df is None:
            raise ValueError("BACデータは必須です。data_dictに'BAC'が存在しません。")
        
        sed_df = data_dict.get("SED")
        if sed_df is not None:
            featured_df = self._feature_extractor.extract_all_parallel(raw_df, sed_df, bac_df)
            del raw_df  # 使用済みのため削除
        else:
            featured_df = raw_df

        # featured_dfをキャッシュに保存
        if self._use_cache and self._cache_manager is not None:
            self._cache_manager.save(
                data_types, year, split_date, featured_df=featured_df
            )

        # データ変換とインデックス設定
        converted_df, featured_df_for_eval = self._convert_and_prepare_data(featured_df, split_date)

        # 時系列分割とカラム選択（split_date指定時）
        if split_date is not None:
            if featured_df_for_eval is None:
                raise ValueError("split_date指定時はfeatured_dfが必要です。")
            train_df, test_df, eval_df = self._split_and_select_columns(converted_df, featured_df_for_eval, split_date)
            
            # キャッシュに保存（converted_dfも保存）
            if self._use_cache and self._cache_manager is not None:
                self._cache_manager.save(
                    data_types, year, split_date, 
                    train_df=train_df, test_df=test_df, eval_df=eval_df,
                    converted_df=converted_df
                )
            
            print(f"\n前処理完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
            return train_df, test_df, eval_df

        return converted_df

    def _load_all_years_sed_bac(self, years: List[int]) -> Tuple[Optional[pd.DataFrame], pd.DataFrame]:
        """
        全年度のSED/BACデータを読み込み・結合
        
        Args:
            years: 年度のリスト
        
        Returns:
            (all_sed_df, all_bac_df) - BACは必須のためNoneにならない
        
        Raises:
            ValueError: BACデータが存在しない場合
        """
        print(f"[_01_] 全年度のSED/BACデータを読み込み・結合中（前走データ抽出用）...")
        all_sed_dfs = []
        all_bac_dfs = []
        for year in years:
            data_dict = self._parquet_loader.load(["SED", "BAC"], year)
            if "SED" in data_dict and data_dict["SED"] is not None:
                all_sed_dfs.append(data_dict["SED"])
            if "BAC" in data_dict and data_dict["BAC"] is not None:
                all_bac_dfs.append(data_dict["BAC"])
        
        # 空のDataFrameを除外してから結合（FutureWarningを回避）
        all_sed_dfs_filtered = [df for df in all_sed_dfs if len(df) > 0]
        all_bac_dfs_filtered = [df for df in all_bac_dfs if len(df) > 0]
        
        # メモリ効率化: 段階的に結合
        if all_sed_dfs_filtered:
            all_sed_df = all_sed_dfs_filtered[0].copy()
            for df in all_sed_dfs_filtered[1:]:
                all_sed_df = pd.concat([all_sed_df, df.copy()], ignore_index=True)
                del df
                import gc
                gc.collect()
        else:
            all_sed_df = None
            
        if all_bac_dfs_filtered:
            all_bac_df = all_bac_dfs_filtered[0].copy()
            for df in all_bac_dfs_filtered[1:]:
                all_bac_df = pd.concat([all_bac_df, df.copy()], ignore_index=True)
                del df
                import gc
                gc.collect()
        else:
            all_bac_df = None
        
        # リストを削除
        del all_sed_dfs, all_bac_dfs, all_sed_dfs_filtered, all_bac_dfs_filtered
        import gc
        gc.collect()
        
        if all_bac_df is None:
            raise ValueError("BACデータは必須です。全年度のBACデータが存在しません。")
        
        print(f"[_01_] 全年度のSEDデータ: {len(all_sed_df):,}件" if all_sed_df is not None else "[_01_] 全年度のSEDデータ: なし")
        print(f"[_01_] 全年度のBACデータ: {len(all_bac_df):,}件")
        return all_sed_df, all_bac_df

    def _process_single_year_features(
        self, year: int, data_types: List[str], all_sed_df: Optional[pd.DataFrame], all_bac_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        単一年度の特徴量抽出を実行
        
        Args:
            year: 年度
            data_types: データタイプのリスト
            all_sed_df: 全年度のSEDデータ（None可）
            all_bac_df: 全年度のBACデータ（必須）
        
        Returns:
            特徴量抽出済みDataFrame
        """
        print(f"\n{'='*80}")
        print(f"[_01_] {year}年のデータを処理中...")
        print(f"{'='*80}")
        
        data_dict = self._parquet_loader.load(data_types, year)
        raw_df = self._jrdb_combiner.combine(data_dict)
        print(f"[_02_] {year}年のデータ結合完了: {len(raw_df):,}件")
        
        print(f"[_03_] {year}年の特徴量追加中（全年度のSED/BACデータを使用）...")
        if all_sed_df is not None:
            featured_df = self._feature_extractor.extract_all_parallel(raw_df, all_sed_df, all_bac_df)
            # メモリ解放
            del raw_df
        else:
            featured_df = raw_df
        del data_dict
        
        import gc
        gc.collect()
        
        print(f"[_03_] {year}年の特徴量抽出完了: {len(featured_df):,}件")
        
        # メモリ効率化: データ型を最適化（早い段階で実行）
        try:
            # 数値カラムの型を最適化
            for col in featured_df.select_dtypes(include=['int64']).columns:
                if featured_df[col].min() >= 0 and featured_df[col].max() <= 2147483647:
                    featured_df[col] = featured_df[col].astype('int32')
            for col in featured_df.select_dtypes(include=['float64']).columns:
                featured_df[col] = pd.to_numeric(featured_df[col], downcast='float')
            gc.collect()
        except Exception as e:
            print(f"警告: データ型最適化でエラーが発生しました（処理は続行）: {e}")
        
        return featured_df

    def _convert_and_prepare_data(
        self, featured_df: pd.DataFrame, split_date: Optional[Union[str, datetime]]
    ) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
        """
        データ変換とインデックス設定を実行
        
        Args:
            featured_df: 特徴量抽出済みDataFrame
            split_date: 時系列分割日時（None可）
        
        Returns:
            (converted_df, featured_df) - split_date未指定時はfeatured_dfはNone
        """
        print("[_04_] データ変換中（キー変換・数値化）...")
        converted_df = self._key_converter.convert(featured_df)
        print("[_04_] データ最適化中...")
        converted_df = self._key_converter.optimize(converted_df)
        print("[_04_] データ変換完了")
        
        if split_date is None:
            del featured_df
            featured_df = None
        
        if "race_key" in converted_df.columns:
            converted_df.set_index("race_key", inplace=True)
            if "start_datetime" in converted_df.columns:
                converted_df = converted_df.sort_values("start_datetime", ascending=True)
        
        return converted_df, featured_df

    def _split_and_select_columns(
        self, converted_df: pd.DataFrame, featured_df: pd.DataFrame, split_date: Union[str, datetime]
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        時系列分割とカラム選択を実行
        
        Args:
            converted_df: 変換済みDataFrame
            featured_df: 特徴量抽出済みDataFrame（評価用データ準備に必要）
            split_date: 時系列分割日時
        
        Returns:
            (train_df, test_df, eval_df)
        """
        print(f"[_05_] 時系列分割中（分割日時: {split_date}）...")
        train_df, test_df = self._time_series_splitter.split(converted_df, split_date)
        print(f"[_05_] 時系列分割完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
        
        print("[_06_] 学習用カラム選択中...")
        train_df = self._column_selector.select_training(train_df)
        test_df = self._column_selector.select_training(test_df)
        print("[_06_] 学習用カラム選択完了")
        
        print("[_06_] 評価用データ準備中...")
        eval_df = self._column_selector.select_evaluation(featured_df)
        if "race_key" in eval_df.columns:
            eval_df.set_index("race_key", inplace=True)
            if "start_datetime" in eval_df.columns:
                eval_df = eval_df.sort_values("start_datetime", ascending=True)
        print("[_06_] 評価用データ準備完了")
        
        return train_df, test_df, eval_df

    def process_multiple_years(
        self,
        data_types: List[str],
        years: List[int],
        split_date: Optional[Union[str, datetime]] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        複数年度のデータを処理（全年度のSED/BACデータを使用して前走データを抽出）
        
        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            split_date: 時系列分割日時（指定時は分割実行）
        
        Returns:
            split_date指定時: (train_df, test_df, eval_df)
            split_date未指定時: converted_df
        
        Raises:
            ValueError: yearsが空の場合、またはBACデータが存在しない場合
        """
        if not years:
            raise ValueError("yearsは空にできません。")
        
        # 全年度のSED/BACデータを事前に読み込み・結合
        all_sed_df, all_bac_df = self._load_all_years_sed_bac(years)
        
        # 年度ごとに分割して処理（メモリ使用量を削減）
        featured_dfs = []
        for year in years:
            featured_df = self._process_single_year_features(year, data_types, all_sed_df, all_bac_df)
            featured_dfs.append(featured_df)
            # 各年度処理後にメモリを解放
            import gc
            gc.collect()
        
        # 全年度のSED/BACデータを削除（使用済み）
        del all_sed_df, all_bac_df
        import gc
        gc.collect()
        
        # 年度ごとの特徴量抽出結果を結合
        print(f"\n{'='*80}")
        print("[_03_] 年度ごとの特徴量抽出結果を結合中...")
        print(f"{'='*80}")
        # 空のDataFrameを除外してから結合（FutureWarningを回避）
        featured_dfs_filtered = [df for df in featured_dfs if len(df) > 0]
        if not featured_dfs_filtered:
            raise ValueError("特徴量抽出結果が空です。")
        featured_df = pd.concat(featured_dfs_filtered, ignore_index=True)
        del featured_dfs
        gc.collect()
        print(f"[_03_] 結合完了: {len(featured_df):,}件")
        
        # データ変換とインデックス設定
        converted_df, featured_df_for_eval = self._convert_and_prepare_data(featured_df, split_date)
        
        # 時系列分割とカラム選択（split_date指定時）
        if split_date is not None:
            if featured_df_for_eval is None:
                raise ValueError("split_date指定時はfeatured_dfが必要です。")
            train_df, test_df, eval_df = self._split_and_select_columns(converted_df, featured_df_for_eval, split_date)
            
            # TODO: 複数年度のキャッシュ機能を実装する場合は、CacheManagerを拡張して
            # キャッシュキーに全年度を含める必要がある。現時点ではキャッシュをスキップする。
            
            print(f"\n前処理完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
            return train_df, test_df, eval_df
        
        return converted_df

