"""full_info_schema.jsonを元に日本語キー→英語キー変換と数値型変換を行う"""

from typing import Dict, Set

import numpy as np
import pandas as pd

from ._03_01_feature_converter import FeatureConverter


class NumericConverter:
    """日本語キー→英語キー変換と数値型変換を行うクラス（staticメソッドのみ）"""

    @staticmethod
    def _get_field_mapping(schema: dict) -> Dict[str, str]:
        """日本語キー → 英語キー（feature_name）のマッピング"""
        mapping = {}
        for col in schema.get("columns", []):
            jp_name = col.get("name")
            feature_name = col.get("feature_name")
            if jp_name and feature_name:
                mapping[jp_name] = feature_name
        return mapping

    @staticmethod
    def _get_numeric_features(schema: dict) -> Set[str]:
        """数値特徴量のセット（英語キー）"""
        numeric = set()
        for col in schema.get("columns", []):
            if col.get("type") == "numeric" or col.get("type") == "integer":
                feature_name = col.get("feature_name")
                if feature_name:
                    numeric.add(feature_name)
        return numeric

    @staticmethod
    def _get_integer_features(schema: dict) -> Set[str]:
        """整数特徴量のセット（整数型にダウンキャスト可能なもの、英語キー）"""
        integer = set()
        for col in schema.get("columns", []):
            col_type = col.get("type")
            feature_name = col.get("feature_name")
            if feature_name and (col_type == "integer" or col_type == "numeric"):
                # 整数型の特徴量を判定
                if any(keyword in feature_name for keyword in ["id", "number", "count", "rank", "frame", "round", "day", "num_horses", "race_num"]):
                    integer.add(feature_name)
        return integer

    @staticmethod
    def convert_to_numeric(df: pd.DataFrame, full_info_schema: dict) -> pd.DataFrame:
        """
        日本語キー→英語キー変換と数値型変換を行う。
        full_info_schema.jsonのfeature_nameを使用して変換。
        
        Args:
            df: 対象のDataFrame（日本語キー）
        
        Returns:
            変換済みDataFrame（英語キー、数値型）
        """
        # add_start_datetime_to_df内でcopy()が実行されるため、ここでのcopy()は不要
        df = FeatureConverter.add_start_datetime_to_df(df)

        # 日本語キー→英語キー変換（full_info_schema.jsonのfeature_nameを使用）
        field_mapping = NumericConverter._get_field_mapping(full_info_schema)
        for jp_name, feature_name in field_mapping.items():
            if jp_name in df.columns and feature_name not in df.columns:
                df[feature_name] = df[jp_name]
                # 元の日本語キーは削除（英語キーに変換済み）
                if jp_name != feature_name:
                    df = df.drop(columns=[jp_name])
        
        # 着順→rank、タイム→timeの変換（full_info_schema.jsonに定義されていないため個別処理）
        if "着順" in df.columns and "rank" not in df.columns:
            df["rank"] = pd.to_numeric(df["着順"], errors="coerce")
            df = df.drop(columns=["着順"])
        if "タイム" in df.columns and "time" not in df.columns:
            df["time"] = df["タイム"].apply(lambda x: FeatureConverter.convert_sed_time_to_seconds(x) if pd.notna(x) else np.nan)
            df = df.drop(columns=["タイム"])

        NumericConverter._add_computed_fields(df)

        # 数値型変換（英語キーに対して実行）
        numeric_features = NumericConverter._get_numeric_features(full_info_schema)
        integer_features = NumericConverter._get_integer_features(full_info_schema)
        for feature_name in numeric_features:
            if feature_name not in df.columns or feature_name == "start_datetime":
                continue
            df[feature_name] = pd.to_numeric(
                df[feature_name],
                errors="coerce",
                downcast="integer" if feature_name in integer_features else None,
            )

        return df

    @staticmethod
    def _add_computed_fields(df: pd.DataFrame) -> None:
        """計算フィールドを追加（ageなど）。df: 対象のDataFrame（in-placeで変更）"""
        # ageは日本語キー「年齢」として既に追加されている可能性があるため、英語キー「age」に変換
        if "age" not in df.columns and "年齢" in df.columns:
            df["age"] = df["年齢"]
        elif "age" not in df.columns:
            if "生年月日" in df.columns and "start_datetime" in df.columns:
                birth_date = pd.to_datetime(df["生年月日"].astype(str), format="%Y%m%d", errors="coerce")
                race_date = pd.to_datetime(df["start_datetime"].astype(str).str[:8], format="%Y%m%d", errors="coerce")
                age = (race_date - birth_date).dt.days / 365.25
                df["age"] = age.round().astype("Int64")
            elif "生年月日" in df.columns and "年月日" in df.columns:
                birth_date = pd.to_datetime(df["生年月日"].astype(str), format="%Y%m%d", errors="coerce")
                race_date = pd.to_datetime(df["年月日"].astype(str), format="%Y%m%d", errors="coerce")
                age = (race_date - birth_date).dt.days / 365.25
                df["age"] = age.round().astype("Int64")

    @staticmethod
    def convert_prev_race_types(df: pd.DataFrame) -> pd.DataFrame:
        """
        前走データのobject型フィールドを数値型に変換。
        注意: この関数はconvert_to_numeric()の後に呼ばれるため、既に英語キーに変換済み。
        
        Args:
            df: 対象のDataFrame（英語キー）
        
        Returns:
            変換済みDataFrame
        """
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()
        try:
            for col in df.columns:
                if not col.startswith("prev_"):
                    continue
                if df[col].dtype == "object" or df[col].dtype.name == "object":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            return df
        finally:
            # この関数内で作成された中間変数は自動的に削除される
            import gc
            gc.collect()
