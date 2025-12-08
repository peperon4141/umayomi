"""スキーマファイルの読み込み処理"""

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from src.jrdb_scraper.entities.jrdb import JRDBDataType


class SchemaFile(str, Enum):
    """スキーマファイル名の定義"""
    FULL_INFO = "_00_full_info_schema.json"
    COMBINED = "_02_combined_schema.json"
    FEATURE_EXTRACTION = "_03_feature_extraction_schema.json"
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
    
    def load_schema(self, schema_file: SchemaFile) -> Dict:
        """スキーマファイルを読み込む（baseDataTypeがあればJRDBDataTypeにキャスト）"""
        schema_path = self._schemas_dir / schema_file.value
        if not schema_path.exists(): raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}") 
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        
        # baseDataTypeがあればJRDBDataTypeにキャスト
        if "baseDataType" in schema and isinstance(schema["baseDataType"], str):
            try: schema["baseDataType"] = JRDBDataType(schema["baseDataType"])
            except ValueError: raise ValueError(f"スキーマのbaseDataType '{schema['baseDataType']}' はJRDBDataTypeに定義されていません。")
        
        return schema

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


