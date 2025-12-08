"""データ型を最適化してメモリ使用量と計算速度を向上させる（float64→float32, int64→int32）"""

import gc
from typing import List

import pandas as pd

class DtypeOptimizer:
    """データ型を最適化するクラス（staticメソッドのみ）"""

    @staticmethod
    def _get_categorical_features(training_schema: dict) -> List[dict]:
        """カテゴリカル特徴量の定義を取得"""
        if "columns" not in training_schema: raise ValueError("training_schemaにcolumnsが定義されていません。スキーマファイルを確認してください。")
        categorical = []
        for col in training_schema["columns"]:
            if "type" not in col: raise ValueError("スキーマのカラム定義にtypeが含まれていません。スキーマファイルを確認してください。")
            if col["type"] == "categorical":
                if "name" not in col: raise ValueError("カテゴリカル特徴量の定義にnameが含まれていません。スキーマファイルを確認してください。")
                feature_name = col["name"]
                categorical.append({"name": feature_name})
        return categorical

    @staticmethod
    def optimize(df: pd.DataFrame, training_schema: dict) -> pd.DataFrame:
        """
        データ型を最適化
        
        Args:
            df: 対象のDataFrame
        
        Returns:
            最適化済みDataFrame
        """
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()
        
        try:
            for col in df.select_dtypes(include=["float64"]).columns:
                df[col] = df[col].astype("float32")

            for col in df.select_dtypes(include=["int64"]).columns:
                col_min, col_max = df[col].min(), df[col].max()
                if -2147483648 <= col_min <= col_max <= 2147483647:
                    df[col] = df[col].astype("int32")

            categorical_features = DtypeOptimizer._get_categorical_features(training_schema)
            for feature_info in categorical_features:
                encoded_name = f"e_{feature_info['name']}"
                if encoded_name in df.columns and df[encoded_name].nunique() / len(df) <= 0.5:
                    df[encoded_name] = df[encoded_name].astype("category")

            return df
        finally:
            # この関数内で作成された中間変数は自動的に削除される
            gc.collect()

    @staticmethod
    def cleanup_object_columns(df: pd.DataFrame) -> pd.DataFrame:
        """
        ラベルエンコーディング後に残ったobject型カラムを削除
        
        Args:
            df: 対象のDataFrame
        
        Returns:
            クリーンアップ済みDataFrame
        """
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()
        try:
            for col in df.columns:
                if col.startswith("prev_") and (df[col].dtype == "object" or df[col].dtype.name == "object"):
                    df = df.drop(columns=[col])
            return df
        finally:
            # この関数内で作成された中間変数は自動的に削除される
            gc.collect()
