"""カテゴリカル特徴量（場コード、天候、馬場状態など）を数値にエンコーディングする"""

import json
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
from sklearn import preprocessing


class LabelEncoder:
    """カテゴリカル特徴量をラベルエンコーディングするクラス"""

    def __init__(self, base_path: Optional[Path] = None):
        """初期化。base_path: プロジェクトのベースパス"""
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        self.schemas_dir = self.base_path / "packages" / "data" / "schemas"
        self.training_schemas_dir = self.schemas_dir / "jrdb_processed"
        self.categories_dir = self.schemas_dir / "categories"
        self._training_schema: Optional[dict] = None
        self._category_mappings: Optional[Dict[str, dict]] = None
        self.label_encoders: Dict[str, preprocessing.LabelEncoder] = {}

    def _load_training_schema(self) -> dict:
        """学習用データスキーマを読み込む"""
        if self._training_schema is None:
            schema_file = self.training_schemas_dir / "training_schema.json"
            if not schema_file.exists():
                raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
            with open(schema_file, "r", encoding="utf-8") as f:
                self._training_schema = json.load(f)
        return self._training_schema

    def _load_category_mappings(self) -> Dict[str, dict]:
        """カテゴリマッピングを読み込む"""
        if self._category_mappings is None:
            mappings = {}
            for category_file in ["course_type.json", "weather.json", "ground_condition.json", "sex.json"]:
                file_path = self.categories_dir / category_file
                if file_path.exists():
                    with open(file_path, "r", encoding="utf-8") as f:
                        cat_data = json.load(f)
                        mappings[cat_data["name"]] = cat_data
            self._category_mappings = mappings
        return self._category_mappings

    def _get_categorical_features(self) -> list[dict]:
        """カテゴリカル特徴量の定義を取得"""
        schema = self._load_training_schema()
        category_mappings = self._load_category_mappings()
        categorical = []
        for col in schema.get("columns", []):
            if col.get("type") == "categorical":
                feature_name = col.get("name")
                if not feature_name:
                    continue
                cat_def = {"name": feature_name}
                category_mapping_name = col.get("category_mapping_name")
                if category_mapping_name and category_mapping_name in category_mappings:
                    cat_data = category_mappings[category_mapping_name]
                    if cat_data.get("type") == "map":
                        cat_def["map"] = cat_data.get("mapping", {})
                    elif cat_data.get("type") == "list":
                        cat_def["list"] = cat_data.get("categories", [])
                categorical.append(cat_def)
        return categorical

    def encode(self, df: pd.DataFrame) -> pd.DataFrame:
        """カテゴリカル特徴量をラベルエンコーディング。df: 対象のDataFrame"""
        df = df.copy()
        encoded_columns = {}
        column_order = list(df.columns)

        categorical_features = self._get_categorical_features()
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
                    if feature_name not in self.label_encoders:
                        self.label_encoders[feature_name] = preprocessing.LabelEncoder()
                        is_numeric = df[feature_name].dtype in ["float64", "float32", "int64", "int32"]
                        # カテゴリカル特徴量のエンコーディングにおいて、欠損値は「未知のカテゴリ」として扱う
                        # これは機械学習の一般的な手法であり、データ不整合ではなく正常な処理
                        feature_values = df[feature_name].astype(str).replace("nan", "__UNKNOWN__") if is_numeric else df[feature_name].fillna("__UNKNOWN__")
                        self.label_encoders[feature_name].fit(feature_values)

                    is_numeric = df[feature_name].dtype in ["float64", "float32", "int64", "int32"]
                    # カテゴリカル特徴量のエンコーディングにおいて、欠損値は「未知のカテゴリ」として扱う
                    # これは機械学習の一般的な手法であり、データ不整合ではなく正常な処理
                    feature_values = df[feature_name].astype(str).replace("nan", "__UNKNOWN__") if is_numeric else df[feature_name].fillna("__UNKNOWN__")
                    encoded_columns[new_column_name] = pd.Series(
                        self.label_encoders[feature_name].transform(feature_values),
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
