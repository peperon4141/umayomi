"""カテゴリカル特徴量（場コード、天候、馬場状態など）を数値にエンコーディングする"""

from typing import Dict

import pandas as pd
from sklearn import preprocessing

class LabelEncoder:
    """カテゴリカル特徴量をラベルエンコーディングするクラス（staticメソッドのみ）"""

    # クラス変数としてラベルエンコーダーを保持
    _label_encoders: Dict[str, preprocessing.LabelEncoder] = {}

    @staticmethod
    def encode(df: pd.DataFrame, training_schema: dict, category_mappings: Dict[str, dict]) -> pd.DataFrame:
        """
        カテゴリカル特徴量をラベルエンコーディング
        
        Args:
            df: 対象のDataFrame
        
        Returns:
            エンコーディング済みDataFrame
        """
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()
        encoded_columns = {}
        column_order = list(df.columns)
        
        try:
            categorical_features = LabelEncoder._get_categorical_features(training_schema, category_mappings)
            for feature_info in categorical_features:
                feature_name = feature_info["name"]
                if feature_name not in df.columns:
                    continue
                if feature_name.startswith("prev_") and "ground_condition" in feature_name:
                    continue

                new_column_name = f"e_{feature_name}"
                try:
                    if "map" in feature_info:
                        encoded_columns[new_column_name] = df[feature_name].map(feature_info["map"]).fillna(-1).astype("category")
                    else:
                        if feature_name not in LabelEncoder._label_encoders:
                            LabelEncoder._label_encoders[feature_name] = preprocessing.LabelEncoder()
                            is_numeric = df[feature_name].dtype in ["float64", "float32", "int64", "int32"]
                            # カテゴリカル特徴量のエンコーディングにおいて、欠損値は「未知のカテゴリ」として扱う
                            # これは機械学習の一般的な手法であり、データ不整合ではなく正常な処理
                            feature_values = df[feature_name].astype(str).replace("nan", "__UNKNOWN__") if is_numeric else df[feature_name].fillna("__UNKNOWN__")
                            LabelEncoder._label_encoders[feature_name].fit(feature_values)

                        is_numeric = df[feature_name].dtype in ["float64", "float32", "int64", "int32"]
                        # カテゴリカル特徴量のエンコーディングにおいて、欠損値は「未知のカテゴリ」として扱う
                        # これは機械学習の一般的な手法であり、データ不整合ではなく正常な処理
                        feature_values = df[feature_name].astype(str).replace("nan", "__UNKNOWN__") if is_numeric else df[feature_name].fillna("__UNKNOWN__")
                        encoded_columns[new_column_name] = pd.Series(
                            LabelEncoder._label_encoders[feature_name].transform(feature_values),
                            index=df.index,
                            dtype="category"
                        )
                except Exception as e:
                    raise

            for new_column_name, encoded_series in encoded_columns.items():
                feature_name = new_column_name[2:]
                if feature_name in column_order:
                    insert_pos = column_order.index(feature_name) + 1
                    column_order.insert(insert_pos, new_column_name)
                else:
                    column_order.append(new_column_name)
                df[new_column_name] = encoded_series

            df = df[column_order]
            return df
        finally:
            # クリーンアップ: 不要なデータを削除
            if 'encoded_columns' in locals():
                del encoded_columns
            import gc
            gc.collect()

    @staticmethod
    def _get_categorical_features(training_schema: dict, category_mappings: Dict[str, dict]) -> list[dict]:
        """カテゴリカル特徴量の定義を取得"""
        categorical = []
        for col in training_schema.get("columns", []):
            if col.get("type") == "categorical":
                feature_name = col.get("name")
                if not feature_name:
                    continue
                cat_def = {"name": feature_name}
                category_mapping_name = col.get("category_mapping_name")
                if category_mapping_name and category_mapping_name in category_mappings:
                    cat_data = category_mappings[category_mapping_name]
                    cat_type = cat_data.get("type")
                    if cat_type == "map":
                        if "mapping" not in cat_data:
                            raise ValueError(f"カテゴリマッピング '{category_mapping_name}' のtypeが'map'ですが、'mapping'が定義されていません。")
                        cat_def["map"] = cat_data["mapping"]
                    elif cat_type == "list":
                        if "categories" not in cat_data:
                            raise ValueError(f"カテゴリマッピング '{category_mapping_name}' のtypeが'list'ですが、'categories'が定義されていません。")
                        cat_def["list"] = cat_data["categories"]
                categorical.append(cat_def)
        return categorical
