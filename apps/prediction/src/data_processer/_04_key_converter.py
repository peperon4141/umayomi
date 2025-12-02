"""データ変換処理（キー変換、数値化、最適化）"""

from pathlib import Path

import pandas as pd

from ._04_03_dtype_optimizer import optimize, cleanup_object_columns
from ._04_02_label_encoder import LabelEncoder
from ._04_01_numeric_converter import convert_to_numeric, convert_prev_race_types


class KeyConverter:
    """キー変換と数値化を行うクラス"""

    def __init__(self, base_path: Path):
        """初期化。base_path: プロジェクトのベースパス"""
        self._base_path = Path(base_path)

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        """日本語キー→英語キー変換と数値化。df: 日本語キーのDataFrame。英語キーのDataFrame（数値化済み）を返す"""
        df = convert_to_numeric(df, base_path=self._base_path)
        df = convert_prev_race_types(df)
        df = LabelEncoder(base_path=self._base_path).encode(df)
        return df

    def optimize(self, df: pd.DataFrame) -> pd.DataFrame:
        """データ型を最適化。df: 変換済みDataFrame。最適化済みDataFrameを返す"""
        df = optimize(df, base_path=self._base_path)
        df = cleanup_object_columns(df)
        return df

