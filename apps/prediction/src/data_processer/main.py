"""メインのオーケストレーター - シンプルで明確なデータ処理フロー"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd

from .cache_manager import CacheManager
from .column_selector import ColumnSelector
from .jrdb_combiner import JrdbCombiner
from .key_converter import KeyConverter
from .npz_loader import NpzLoader
from .time_series_splitter import TimeSeriesSplitter
from .feature_extractor import FeatureExtractor


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

        self._npz_loader = NpzLoader(self._base_path / "apps" / "prediction" / "notebooks" / "data")
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
        print("データ読み込みと前処理を開始します...")
        data_dict = self._npz_loader.load(data_types, year)
        print(f"データ読み込み完了: {len(data_dict)}件のデータタイプ")
        
        print("データ結合中...")
        raw_df = self._jrdb_combiner.combine(data_dict)
        print(f"データ結合完了: {len(raw_df):,}件")

        # ステップ2: 特徴量追加（並列処理）
        sed_df = data_dict.get("SED")
        bac_df = data_dict.get("BAC")
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

        # ステップ3: データ変換
        print("データ変換中（キー変換・数値化）...")
        converted_df = self._key_converter.convert(featured_df)
        print("データ最適化中...")
        converted_df = self._key_converter.optimize(converted_df)
        print("データ変換完了")
        
        # split_date未指定時はfeatured_dfを削除（eval_df作成時に必要なので、指定時は保持）
        if split_date is None:
            del featured_df

        # インデックス設定
        if "race_key" in converted_df.columns:
            converted_df.set_index("race_key", inplace=True)
            if "start_datetime" in converted_df.columns:
                converted_df = converted_df.sort_values("start_datetime", ascending=True)

        # ステップ4: 時系列分割とカラム選択（split_date指定時）
        if split_date is not None:
            print(f"時系列分割中（分割日時: {split_date}）...")
            train_df, test_df = self._time_series_splitter.split(converted_df, split_date)
            print(f"時系列分割完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
            
            print("学習用カラム選択中...")
            train_df = self._column_selector.select_training(train_df)
            test_df = self._column_selector.select_training(test_df)
            print("学習用カラム選択完了")
            
            print("評価用データ準備中...")
            eval_df = self._column_selector.select_evaluation(featured_df)
            if "race_key" in eval_df.columns:
                eval_df.set_index("race_key", inplace=True)
                if "start_datetime" in eval_df.columns:
                    eval_df = eval_df.sort_values("start_datetime", ascending=True)
            print("評価用データ準備完了")
            
            # キャッシュに保存（converted_dfも保存）
            if self._use_cache and self._cache_manager is not None:
                self._cache_manager.save(
                    data_types, year, split_date, 
                    train_df=train_df, test_df=test_df, eval_df=eval_df,
                    converted_df=converted_df
                )
            
            print(f"\n前処理完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
            return train_df, test_df, eval_df

        # キャッシュに保存（split_date未指定時、converted_dfは既にdataとして保存済み）
        # featured_dfは既に保存済み

        return converted_df

