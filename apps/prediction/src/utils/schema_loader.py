"""スキーマファイルの読み込み処理"""

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.jrdb_scraper.entities.jrdb import JRDBDataType


@dataclass
class Column:
    """スキーマのカラム定義"""
    name: str
    source: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    feature_name: Optional[str] = None
    use_for_training: Optional[bool] = None
    jrdb_name: Optional[str] = None
    data_types: Optional[List[str]] = None
    is_computed: Optional[bool] = None
    category_mapping_name: Optional[str] = None
    required: Optional[bool] = None
    category: Optional[str] = None
    evaluation_metrics: Optional[List[str]] = None


@dataclass
class Schema:
    """スキーマクラス（description、columns、identifierColumnsを持つ基本クラス）"""
    description: str
    columns: List[Column]
    identifierColumns: List[str]
    target_variable: Optional[Dict] = None
    merge_keys: Optional[Dict] = None
    evaluation_metrics: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Schema":
        """辞書からSchemaインスタンスを作成"""
        if "description" not in data: raise ValueError("スキーマにdescriptionが定義されていません。")
        if "columns" not in data: raise ValueError("スキーマにcolumnsが定義されていません。")
        if "identifierColumns" not in data: raise ValueError("スキーマにidentifierColumnsが定義されていません。")
        columns = [Column(**col) if isinstance(col, dict) else col for col in data["columns"]]
        target_variable = data.get("target_variable")
        merge_keys = data.get("merge_keys")
        evaluation_metrics = data.get("evaluation_metrics")
        return cls(description=data["description"], columns=columns, identifierColumns=data["identifierColumns"], target_variable=target_variable, merge_keys=merge_keys, evaluation_metrics=evaluation_metrics)
    
    def _has_index(self, df: pd.DataFrame) -> bool:
        """インデックスが正しく設定されているか検証"""
        return isinstance(df.index, pd.MultiIndex) and list(df.index.names) == self.identifierColumns

    def _has_columns(self, df: pd.DataFrame) -> bool:
        """スキーマで定義されたカラムが実際のDataFrameに存在するか検証（サフィックス付きも含む、インデックスも考慮）"""
        schema_cols = {col.name for col in self.columns}
        actual_cols = set(df.columns)
        # インデックスに設定されているカラムも考慮
        if isinstance(df.index, pd.MultiIndex):
            actual_cols.update(df.index.names)
        elif df.index.name is not None:
            actual_cols.add(df.index.name)
        missing = [col for col in schema_cols if col not in actual_cols and not any(c.startswith(f"{col}_") for c in actual_cols)]
        return len(missing) == 0

    def validate(self, df: pd.DataFrame) -> None:
        """DataFrameをスキーマに基づいて検証"""
        # インデックスがMultiIndexの場合は検証、そうでない場合はスキップ（reset_index後の状態）
        if isinstance(df.index, pd.MultiIndex):
            if not self._has_index(df):
                actual = list(df.index.names) if isinstance(df.index, pd.MultiIndex) else type(df.index).__name__
                raise ValueError(f"MultiIndexが正しく設定されていません。期待: {self.identifierColumns}, 実際: {actual}")
        
        if not self._has_columns(df):
            schema_cols = {col.name for col in self.columns}
            actual_cols = set(df.columns)
            missing = [col for col in schema_cols if col not in actual_cols and not any(c.startswith(f"{col}_") for c in actual_cols)]
            raise ValueError(f"スキーマで定義されたカラムが存在しません: {missing[:20]}")


class SchemaFile(str, Enum):
    """スキーマファイル名の定義"""
    FULL_INFO = "_00_full_info_schema.json"
    COMBINED = "_02_combined_schema.json"
    FEATURE_EXTRACTION = "_03_feature_extraction_schema.json"
    PREVIOUS_RACE_EXTRACTOR_02 = "_03_02_previous_race_extractor_schema.json"
    HORSE_STATISTICS = "_03_horse_statistics_schema.json"
    JOCKEY_STATISTICS = "_03_jockey_statistics_schema.json"
    TRAINER_STATISTICS = "_03_trainer_statistics_schema.json"
    PREVIOUS_RACE_EXTRACTOR = "_03_previous_race_extractor_schema.json"
    TRAINING = "_04_training_schema.json"
    KEY_MAPPING = "_04_key_mapping_schema.json"
    COLUMN_SELECTION = "_06_column_selection_schema.json"
    EVALUATION = "_06_evaluation_schema.json"


class SchemaLoader:
    """スキーマファイルの読み込みを担当するクラス"""

    def __init__(self, schemas_base_path: Path):
        """初期化（schemas_base_path: スキーマディレクトリのベースパス）"""
        if schemas_base_path is None: raise ValueError('schemas_base_pathは必須です')
        self._schemas_base_path = Path(schemas_base_path)
        self._schemas_dir = self._schemas_base_path / "jrdb_processed"
        self._categories_dir = self._schemas_base_path / "categories"
    
    def load_schema(self, schema_file: SchemaFile) -> Schema:
        """スキーマファイルを読み込んでSchemaインスタンスを返す"""
        schema_path = self._schemas_dir / schema_file.value
        if not schema_path.exists(): raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}") 
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_dict = json.load(f)
        
        return Schema.from_dict(schema_dict)
    
    def load_schema_dict(self, schema_file: SchemaFile) -> Dict:
        """スキーマファイルを辞書として読み込む（処理ファイルで追加属性が必要な場合用）"""
        schema_path = self._schemas_dir / schema_file.value
        if not schema_path.exists(): raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}") 
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_dict = json.load(f)
        
        # baseDataTypeがあればJRDBDataTypeにキャスト
        if "baseDataType" in schema_dict and isinstance(schema_dict["baseDataType"], str):
            try: schema_dict["baseDataType"] = JRDBDataType(schema_dict["baseDataType"])
            except ValueError: raise ValueError(f"スキーマのbaseDataType '{schema_dict['baseDataType']}' はJRDBDataTypeに定義されていません。")
        
        return schema_dict

    def load_category_mappings(self) -> Dict[str, dict]:
        """
        カテゴリマッピングを読み込む
        
        Returns:
            カテゴリ名をキー、カテゴリデータを値とする辞書
        """
        mappings = {}
        category_files = ["course_type.json", "weather.json", "ground_condition.json", "sex.json"]
        
        for category_file in category_files:
            file_path = self._categories_dir / category_file
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    cat_data = json.load(f)
                    mappings[cat_data["name"]] = cat_data
        
        return mappings


