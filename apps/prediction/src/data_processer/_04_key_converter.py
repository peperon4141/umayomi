"""データ変換処理（キー変換、数値化、最適化）"""

import pandas as pd

from ._04_03_dtype_optimizer import DtypeOptimizer
from ._04_02_label_encoder import LabelEncoder
from ._04_01_numeric_converter import NumericConverter


class KeyConverter:
    """キー変換と数値化を行うクラス（staticメソッドのみ）"""

    @staticmethod
    def convert(df: pd.DataFrame, full_info_schema: dict, training_schema: dict, category_mappings: dict) -> pd.DataFrame:
        """
        日本語キー→英語キー変換と数値化
        
        Args:
            df: 日本語キーのDataFrame
            full_info_schema: full_info_schema.jsonの内容
            training_schema: training_schema.jsonの内容
            category_mappings: カテゴリマッピングの辞書
        
        Returns:
            英語キーのDataFrame（数値化済み）
        """
        df = NumericConverter.convert_to_numeric(df, full_info_schema)
        df = NumericConverter.convert_prev_race_types(df)
        df = LabelEncoder.encode(df, training_schema, category_mappings)
        return df

    @staticmethod
    def optimize(df: pd.DataFrame, training_schema: dict) -> pd.DataFrame:
        """
        データ型を最適化
        
        Args:
            df: 変換済みDataFrame
            training_schema: training_schema.jsonの内容
        
        Returns:
            最適化済みDataFrame
        """
        df = DtypeOptimizer.optimize(df, training_schema)
        df = DtypeOptimizer.cleanup_object_columns(df)
        return df

