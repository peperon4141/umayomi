"""スキーマファイルの読み込み処理"""

import json
from pathlib import Path
from typing import Dict, Optional


class SchemaLoader:
    """スキーマファイルの読み込みを担当するクラス"""

    def __init__(self, schemas_base_path: Optional[Path] = None):
        """
        初期化
        
        Args:
            schemas_base_path: スキーマディレクトリのベースパス（例: packages/data/schemas）
                              Noneの場合は自動検出
        """
        if schemas_base_path is None:
            # プロジェクトルートを自動検出（このファイルから5階層上: src/utils -> src -> prediction -> apps -> umayomi）
            project_root = Path(__file__).parent.parent.parent.parent.parent
            schemas_base_path = project_root / "packages" / "data" / "schemas"
        
        self._schemas_base_path = Path(schemas_base_path)
        self._schemas_dir = self._schemas_base_path / "jrdb_processed"
        self._categories_dir = self._schemas_base_path / "categories"

    def load_full_info_schema(self) -> Dict:
        """
        full_info_schema.jsonを読み込む
        
        Returns:
            スキーマ情報の辞書
        """
        schema_path = self._schemas_dir / "full_info_schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_training_schema(self) -> Dict:
        """
        training_schema.jsonを読み込む
        
        Returns:
            スキーマ情報の辞書
        """
        schema_path = self._schemas_dir / "training_schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_evaluation_schema(self) -> Dict:
        """
        evaluation_schema.jsonを読み込む
        
        Returns:
            スキーマ情報の辞書
        """
        schema_path = self._schemas_dir / "evaluation_schema.json"
        if not schema_path.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_path}")
        
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

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

