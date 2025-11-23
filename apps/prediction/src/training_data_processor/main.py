"""学習前処理の全ステップを統合し、一括実行するオーケストレーター"""

from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd
from tqdm import tqdm

from .column_filter import ColumnFilter
from .data_splitter import DataSplitter
from . import dtype_optimizer
from .jrdb_processor import JrdbProcessor
from .label_encoder import LabelEncoder
from . import numeric_converter
from . import previous_race_extractor
from . import statistical_feature_calculator

class TrainingDataProcessor:
    """学習前処理の全ステップを統合するオーケストレータークラス"""

    def __init__(
        self,
        base_path: Optional[Union[str, Path]] = None,
    ):
        """初期化。base_path: プロジェクトのベースパス"""
        self._base_path = Path(base_path) if base_path is not None else Path(__file__).parent.parent.parent.parent

        self._jrdb_processor = JrdbProcessor(base_path=self._base_path)
        self._label_encoder = LabelEncoder(base_path=self._base_path)
        self._data_splitter = DataSplitter()
        self._column_filter = ColumnFilter(self._base_path)

    def process(
        self,
        base_path: Union[str, Path],
        data_types: List[str],
        years: Optional[List[int]] = None,
        split_date: Optional[Union[str, pd.Timestamp]] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        データの読み込みから前処理まで一括実行。
        base_path: データのベースパス、data_types: データタイプのリスト、years: 年リスト、
        split_date: 時系列分割日時（指定時は分割実行）
        """
        base_path = Path(base_path)

        if years is None: years = [2024]

        year = years[0]

        data_dict = {}
        for data_type in tqdm(data_types, desc="データタイプ読み込み"):
            try:
                data_dict[data_type] = self._jrdb_processor.load_data(data_type, year, base_path)
            except Exception as e:
                if data_type == "SEC" and "SED" in data_types:
                    continue
                raise ValueError(f"データタイプ '{data_type}' の読み込みに失敗しました: {e}")

        missing_types = [dt for dt in data_types if dt not in data_dict and (dt != "SEC" or "SED" not in data_dict)]
        if missing_types:
            raise ValueError(f"指定されたデータタイプが存在しません: {missing_types}。読み込まれたデータタイプ: {', '.join(data_dict.keys())}")

        combined_df = self._jrdb_processor.combine_data(data_dict)

        sed_df = data_dict.get("SED")
        bac_df = data_dict.get("BAC")
        if sed_df is not None:
            combined_df = previous_race_extractor.extract(combined_df, sed_df, bac_df)
            combined_df = statistical_feature_calculator.calculate(combined_df, sed_df, bac_df)

        # full_data_df（日本語キー）を保存（評価用）
        # full_info_schema.jsonで定義されている全カラム（日本語キー）のみを取得
        full_data_df = combined_df.copy()
        jp_cols = self._column_filter.get_all_japanese_columns(full_data_df)
        if jp_cols:
            # full_info_schema.jsonで定義されているカラムのみを選択
            full_data_df = full_data_df[jp_cols].copy()
        if "race_key" in full_data_df.columns:
            full_data_df.set_index("race_key", inplace=True)
            if "start_datetime" in full_data_df.columns:
                full_data_df = full_data_df.sort_values("start_datetime", ascending=True)

        # training_data_df（英語キー）を作成（学習用）
        training_data_df = numeric_converter.convert_to_numeric(combined_df, base_path=self._base_path)
        training_data_df = numeric_converter.convert_prev_race_types(training_data_df)
        training_data_df = self._label_encoder.encode(training_data_df)
        training_data_df = dtype_optimizer.optimize(training_data_df, base_path=self._base_path)
        training_data_df = dtype_optimizer.cleanup_object_columns(training_data_df)

        if "race_key" in training_data_df.columns:
            training_data_df.set_index("race_key", inplace=True)
            if "start_datetime" in training_data_df.columns:
                training_data_df = training_data_df.sort_values("start_datetime", ascending=True)

        if split_date is not None:
            train_df, test_df = self._data_splitter.split_train_test(training_data_df, split_date)

            train_df = self._column_filter.filter_training_columns(train_df)
            test_df = self._column_filter.filter_training_columns(test_df)
            
            if 'rank' not in train_df.columns:
                raise ValueError("train_dfにrank列が含まれていません。filter_training_columns()でtarget_variableが含まれるはずです。")
            if 'rank' not in test_df.columns:
                raise ValueError("test_dfにrank列が含まれていません。filter_training_columns()でtarget_variableが含まれるはずです。")

            return train_df, test_df, full_data_df

        return training_data_df
