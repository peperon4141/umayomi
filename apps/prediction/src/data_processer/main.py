"""メインのオーケストレーター - シンプルで明確なデータ処理フロー"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd

from .column_selector import ColumnSelector
from .jrdb_combiner import JrdbCombiner
from .key_converter import KeyConverter
from .npz_loader import NpzLoader
from .time_series_splitter import TimeSeriesSplitter
from .feature_extractor import FeatureExtractor


class DataProcessor:
    """データ処理のメインオーケストレーター"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """初期化。base_path: プロジェクトのベースパス（デフォルト: プロジェクトルート）"""
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self._base_path = Path(base_path)

        self._npz_loader = NpzLoader(self._base_path / "apps" / "prediction" / "notebooks" / "data")
        self._jrdb_combiner = JrdbCombiner(self._base_path)
        self._feature_extractor = FeatureExtractor()
        self._key_converter = KeyConverter(self._base_path)
        self._time_series_splitter = TimeSeriesSplitter()
        self._column_selector = ColumnSelector(self._base_path)

    def process(
        self,
        data_types: List[str],
        year: int = 2024,
        split_date: Optional[Union[str, datetime]] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """データ処理の全ステップを実行。data_types: データタイプのリスト、year: 年度、split_date: 時系列分割日時（指定時は分割実行）。split_date指定時は(train_df, test_df, eval_df)、未指定時はconverted_dfを返す"""
        # ステップ1: データ読み込みと結合
        print("データ読み込みと前処理を開始します...")
        data_dict = self._npz_loader.load(data_types, year)
        print(f"データ読み込み完了: {len(data_dict)}件のデータタイプ")
        
        print("データ結合中...")
        raw_df = self._jrdb_combiner.combine(data_dict)
        print(f"データ結合完了: {len(raw_df):,}件")

        # ステップ2: 特徴量追加
        sed_df = data_dict.get("SED")
        bac_df = data_dict.get("BAC")
        if sed_df is not None:
            print("前走データ抽出中...")
            featured_df = self._feature_extractor.extract_previous_races(raw_df, sed_df, bac_df)
            print("前走データ抽出完了")
            
            print("統計特徴量計算中...")
            featured_df = self._feature_extractor.extract_statistics(featured_df, sed_df, bac_df)
            print("統計特徴量計算完了")
        else:
            featured_df = raw_df

        # ステップ3: データ変換
        print("データ変換中（キー変換・数値化）...")
        converted_df = self._key_converter.convert(featured_df)
        print("データ最適化中...")
        converted_df = self._key_converter.optimize(converted_df)
        print("データ変換完了")

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
            
            print(f"\n前処理完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
            return train_df, test_df, eval_df

        return converted_df

