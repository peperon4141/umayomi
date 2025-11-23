"""データ変換処理（キー変換、数値化、最適化）"""

import pandas as pd

from . import dtype_optimizer, label_encoder, numeric_converter


class KeyConverter:
    """キー変換と数値化を行うクラス"""

    def __init__(self, base_path):
        """初期化。base_path: プロジェクトのベースパス"""
        self._base_path = base_path

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        """日本語キー→英語キー変換と数値化。df: 日本語キーのDataFrame。英語キーのDataFrame（数値化済み）を返す"""
        df = numeric_converter.convert_to_numeric(df, base_path=self._base_path)
        df = numeric_converter.convert_prev_race_types(df)
        df = label_encoder.LabelEncoder(base_path=self._base_path).encode(df)
        return df

    def optimize(self, df: pd.DataFrame) -> pd.DataFrame:
        """データ型を最適化。df: 変換済みDataFrame。最適化済みDataFrameを返す"""
        df = dtype_optimizer.optimize(df, base_path=self._base_path)
        df = dtype_optimizer.cleanup_object_columns(df)
        return df

