"""メインのオーケストレーター - シンプルで明確なデータ処理フロー"""

import gc
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd

from src.utils.cache_manager import CacheManager
from src.utils.schema_loader import SchemaLoader
from src.utils.parquet_loader import ParquetLoader
from ._06_column_selector import ColumnSelector
from ._02_jrdb_combiner import JrdbCombiner
from ._04_key_converter import KeyConverter
from ._05_time_series_splitter import TimeSeriesSplitter
from ._03_feature_extractor import FeatureExtractor

# 使用するデータタイプの定数定義
_DATA_TYPES = [
    'BAC',  # 番組データ（レース条件・出走馬一覧）
    'KYI',  # 競走馬データ（牧場先情報付き・最も詳細）
    'SED',  # 成績速報データ（過去の成績・前走データ抽出に使用）
    'UKC',  # 馬基本データ（血統登録番号・性別・生年月日・血統情報）
    'TYB',  # 直前情報データ（出走直前の馬の状態・当日予想に最重要）
]


class DataProcessor:
    """データ処理のメインオーケストレーター"""

    def __init__(
        self,
        base_path: Path,
        parquet_base_path: Path,
        use_cache: bool = True,
    ):
        """
        初期化
        
        Args:
            base_path: プロジェクトルートパス
            parquet_base_path: Parquetファイルのベースパス
            use_cache: キャッシュを使用するかどうか（デフォルト: True）
        """
        self._base_path = Path(base_path)
        self._parquet_base_path = Path(parquet_base_path)
        
        # スキーマローダーを初期化
        schemas_base_path = self._base_path / "packages" / "data" / "schemas"
        self._schema_loader = SchemaLoader(schemas_base_path)
        # スキーマを読み込み（キャッシュとして保持）
        self._full_info_schema = self._schema_loader.load_full_info_schema()
        self._training_schema = self._schema_loader.load_training_schema()
        self._evaluation_schema = self._schema_loader.load_evaluation_schema()
        self._category_mappings = self._schema_loader.load_category_mappings()
        
        # Parquetローダーを初期化
        self._parquet_loader = ParquetLoader(self._parquet_base_path)
        
        # キャッシュマネージャーを初期化（staticなパスを持つ）
        prediction_app_path = self._base_path / "apps" / "prediction"
        self._cache_manager = CacheManager(prediction_app_path) if use_cache else None
        self._use_cache = use_cache

    def _load_sed_bac_for_year(self, target_year: int, available_years: Optional[List[int]] = None) -> Tuple[Optional[pd.DataFrame], pd.DataFrame]:
        """
        指定年度の前走データ抽出に必要なSED/BACデータを読み込み
        
        処理対象年度より前の年度のデータを読み込む（前走データ抽出用）
        
        Args:
            target_year: 処理対象年度
            available_years: 利用可能な年度のリスト（Noneの場合は、処理対象年度より前の年度を自動検出）
        
        Returns:
            (sed_df, bac_df) - BACは必須のためNoneにならない
        
        Raises:
            ValueError: BACデータが存在しない場合
        """
        # 処理対象年度より前の年度のデータを読み込む
        if available_years is not None:
            previous_years = [y for y in available_years if y < target_year]
        else:
            # 利用可能な年度のリストが指定されていない場合、処理対象年度より前の年度を自動検出
            # 最大5年前まで検索（前走データは最大5走前まで必要）
            previous_years = [y for y in range(target_year - 5, target_year) if y >= 2000]
        
        if not previous_years:
            # 前年度のデータがない場合は、処理対象年度のデータのみを使用
            previous_years = [target_year]
        
        print(f"[_01_] {target_year}年の前走データ抽出用にSED/BACデータを読み込み中（対象年度: {previous_years}）...")
        
        sed_dfs = []
        bac_dfs = []
        try:
            for year in previous_years:
                try:
                    data_dict = self._parquet_loader.load_parquet_files(["SED", "BAC"], year)
                    if "SED" in data_dict and data_dict["SED"] is not None and len(data_dict["SED"]) > 0:
                        sed_dfs.append(data_dict["SED"])
                    if "BAC" in data_dict and data_dict["BAC"] is not None and len(data_dict["BAC"]) > 0:
                        bac_dfs.append(data_dict["BAC"])
                except (FileNotFoundError, ValueError):
                    # 年度のデータが存在しない場合はスキップ
                    continue
            
            # 空のDataFrameを除外
            sed_dfs = [df for df in sed_dfs if len(df) > 0]
            bac_dfs = [df for df in bac_dfs if len(df) > 0]
            
            # 段階的に結合（コピーを最小化）
            sed_df = None
            if sed_dfs:
                sed_df = sed_dfs[0]  # 最初のDataFrameは参照を使用（コピーしない）
                for df in sed_dfs[1:]:
                    sed_df = pd.concat([sed_df, df], ignore_index=True)
                    del df
                    gc.collect()
            
            bac_df = None
            if bac_dfs:
                bac_df = bac_dfs[0]  # 最初のDataFrameは参照を使用（コピーしない）
                for df in bac_dfs[1:]:
                    bac_df = pd.concat([bac_df, df], ignore_index=True)
                    del df
                    gc.collect()
            
            # リストを削除
            del sed_dfs, bac_dfs
            gc.collect()
            
            if bac_df is None:
                raise ValueError(f"BACデータは必須です。{target_year}年の前走データ抽出用のBACデータが存在しません。")
            
            print(f"[_01_] {target_year}年用SEDデータ: {len(sed_df):,}件" if sed_df is not None else f"[_01_] {target_year}年用SEDデータ: なし")
            print(f"[_01_] {target_year}年用BACデータ: {len(bac_df):,}件")
            return sed_df, bac_df
        finally:
            # クリーンアップ: 中間データを削除
            if 'sed_dfs' in locals():
                del sed_dfs
            if 'bac_dfs' in locals():
                del bac_dfs
            gc.collect()

    def _process_single_year_features(
        self, year: int, available_years: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        単一年度の特徴量抽出を実行
        
        Args:
            year: 年度
            available_years: 利用可能な年度のリスト（前走データ抽出用、Noneの場合は自動検出）
        
        Returns:
            特徴量抽出済みDataFrame
        """
        print(f"\n{'='*80}")
        print(f"[_01_] {year}年のデータを処理中...")
        print(f"{'='*80}")
        
        # 必要なデータを都度読み込む
        # まずKYIとBACを読み込む（結合のベースに必要・必須）
        kyi_df = self._parquet_loader.load_annual_pack_parquet("KYI", year)
        bac_df = self._parquet_loader.load_annual_pack_parquet("BAC", year)
        ukc_df = self._parquet_loader.load_annual_pack_parquet("UKC", year)
        tyb_df = self._parquet_loader.load_annual_pack_parquet("TYB", year)
        
        # 結合処理を実行（結合時のみdata_dictを作成）
        raw_df = JrdbCombiner.combine({
            "KYI": kyi_df,
            "BAC": bac_df,
            "UKC": ukc_df,
            "TYB": tyb_df,
        }, self._full_info_schema)
        
        # 結合後は不要なDataFrameを削除（bac_dfは後で使用するため保持）
        del kyi_df, ukc_df, tyb_df
        gc.collect()
        print(f"[_02_] {year}年のデータ結合完了: {len(raw_df):,}件")
        
        # 前走データ抽出用のSED/BACデータを読み込み（必要な年度のみ）
        sed_df, bac_df = self._load_sed_bac_for_year(year, available_years)
        
        # 処理対象年度のSEDデータも読み込む（特徴量抽出に必要・_DATA_TYPESに含まれているため、存在することが期待される）
        if sed_df is None:
            sed_df = self._parquet_loader.load_annual_pack_parquet("SED", year)
        
        print(f"[_03_] {year}年の特徴量追加中...")
        try:
            # SEDは必須データなので、存在しない場合は既に例外が投げられている
            featured_df = FeatureExtractor.extract_all_parallel(raw_df, sed_df, bac_df)
            # メモリ解放
            del raw_df, sed_df, bac_df
            
            gc.collect()
            
            print(f"[_03_] {year}年の特徴量抽出完了: {len(featured_df):,}件")
            
            return featured_df
        finally:
            # クリーンアップ: 不要なデータを削除
            if 'raw_df' in locals():
                del raw_df
            if 'sed_df' in locals():
                del sed_df
            if 'bac_df' in locals():
                del bac_df
            gc.collect()

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
        converted_df = KeyConverter.convert(featured_df, self._full_info_schema, self._training_schema, self._category_mappings)
        print("[_04_] データ最適化中...")
        converted_df = KeyConverter.optimize(converted_df, self._training_schema)
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
        train_df, test_df = TimeSeriesSplitter.split(converted_df, split_date)
        print(f"[_05_] 時系列分割完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
        
        print("[_06_] 学習用カラム選択中...")
        train_df = ColumnSelector.select_training(train_df, self._full_info_schema, self._training_schema)
        test_df = ColumnSelector.select_training(test_df, self._full_info_schema, self._training_schema)
        print("[_06_] 学習用カラム選択完了")
        
        print("[_06_] 評価用データ準備中...")
        eval_df = ColumnSelector.select_evaluation(featured_df, self._evaluation_schema)
        if "race_key" in eval_df.columns:
            eval_df.set_index("race_key", inplace=True)
            if "start_datetime" in eval_df.columns:
                eval_df = eval_df.sort_values("start_datetime", ascending=True)
        print("[_06_] 評価用データ準備完了")
        
        return train_df, test_df, eval_df

    def process_multiple_years(
        self,
        years: List[int],
        split_date: Optional[Union[str, datetime]] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        複数年度のデータを処理（全年度のSED/BACデータを使用して前走データを抽出）
        
        Args:
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
        
        # 年度ごとに分割して処理（メモリ使用量を削減）
        # 各年度で必要なデータだけを読み込む
        featured_dfs = []
        try:
            for i, year in enumerate(years):
                # 前走データ抽出用に、処理対象年度より前の年度も含めたリストを渡す
                # ただし、利用可能な年度を自動検出する場合はNoneを渡す
                year_featured_df = self._process_single_year_features(year, available_years=years)
                if year_featured_df is not None and len(year_featured_df) > 0:
                    featured_dfs.append(year_featured_df)
                
                # 各年度処理後にメモリを解放
                gc.collect()
            
            # 年度ごとの特徴量抽出結果を結合
            print(f"\n{'='*80}")
            print("[_03_] 年度ごとの特徴量抽出結果を結合中...")
            print(f"{'='*80}")
            
            if not featured_dfs:
                raise ValueError("特徴量抽出結果が空です。")
            
            # 段階的に結合してメモリ使用量を削減
            if len(featured_dfs) == 1:
                featured_df = featured_dfs[0]
            else:
                featured_df = featured_dfs[0]  # 最初のDataFrameは参照を使用
                for i, df in enumerate(featured_dfs[1:], 1):
                    featured_df = pd.concat([featured_df, df], ignore_index=True)
                    del df
                    if i % 2 == 0:  # 2つ結合するごとにガベージコレクション
                        gc.collect()
            
            print(f"[_03_] 結合完了: {len(featured_df):,}件")
        finally:
            # クリーンアップ: 中間データを削除
            if 'featured_dfs' in locals():
                del featured_dfs
            gc.collect()
        
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

