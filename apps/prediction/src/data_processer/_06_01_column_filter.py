"""学習用データの必要なカラムを選択し、評価用カラムを識別する"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Set, Union

import pandas as pd

logger = logging.getLogger(__name__)


class ColumnFilter:
    """学習用データの必要なカラムを選択するクラス"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """初期化。base_path: プロジェクトのベースパス（デフォルト: 現在のディレクトリ）"""
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        self.schemas_dir = self.base_path / "packages" / "data" / "schemas" / "jrdb_processed"
        self._full_info_schema: Optional[dict] = None
        self._training_columns: Optional[Set[str]] = None
        self._evaluation_schema: Optional[dict] = None

    def load_full_info_schema(self) -> dict:
        """full_info_schema.jsonを読み込む"""
        if self._full_info_schema is None:
            schema_file = self.schemas_dir / "full_info_schema.json"
            if not schema_file.exists():
                raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
            with open(schema_file, "r", encoding="utf-8") as f:
                self._full_info_schema = json.load(f)
        return self._full_info_schema

    def load_training_schema(self) -> dict:
        """training_schema.jsonを読み込む"""
        schema_file = self.schemas_dir / "training_schema.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_training_columns(self) -> Set[str]:
        """学習用データの必要なカラム名のセットを取得（英語キー、use_for_training=trueのカラム）"""
        if self._training_columns is None:
            schema = self.load_full_info_schema()
            # use_for_training=trueのカラムのfeature_nameを取得
            training_columns = set()
            for col in schema.get("columns", []):
                if col.get("use_for_training", False):
                    feature_name = col.get("feature_name")
                    if feature_name:
                        training_columns.add(feature_name)
            # rank（ターゲット変数）も追加
            training_columns.add("rank")
            self._training_columns = training_columns
        return self._training_columns

    def filter_training_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        学習用データの必要なカラムを選択。
        
        Args:
            df: 対象のDataFrame
            
        Returns:
            学習用カラムが選択されたDataFrame（ターゲット変数を含む、インデックス名も保持）
        """
        training_columns = self.get_training_columns()  # これでtarget_variableも含まれる
        available_columns = [col for col in training_columns if col in df.columns]
        missing_columns = training_columns - set(df.columns)
        
        # ターゲット変数が欠けている場合はエラー
        schema = self.load_training_schema()
        target_variable = schema.get("target_variable", {})
        target_name = target_variable.get("name")
        if target_name and target_name not in df.columns:
            raise ValueError(f"ターゲット変数 '{target_name}' がDataFrameに存在しません。学習時に必須です。")
        
        if missing_columns:
            logger.warning(f"学習用スキーマに定義されているが、データに存在しないカラム: {sorted(missing_columns)}")
        
        # カラムを選択し、インデックス名を保持
        result = df[available_columns].copy()
        result.index.name = df.index.name  # インデックス名を明示的に保持
        return result

    def get_all_columns(self, df: pd.DataFrame) -> List[str]:
        """full_info_schema.jsonの全カラム（英語キー）を取得"""
        schema = self.load_full_info_schema()
        all_cols = []
        for col in schema.get("columns", []):
            feature_name = col.get("feature_name")
            if feature_name and feature_name in df.columns:
                all_cols.append(feature_name)
        return all_cols

    def get_all_japanese_columns(self, df: pd.DataFrame) -> List[str]:
        """full_info_schema.jsonの全カラム（日本語キー）を取得"""
        schema = self.load_full_info_schema()
        all_cols = []
        for col in schema.get("columns", []):
            jp_name = col.get("name")
            if jp_name and jp_name in df.columns:
                all_cols.append(jp_name)
        return all_cols

    def load_evaluation_schema(self) -> dict:
        """evaluation_schema.jsonを読み込む"""
        if self._evaluation_schema is None:
            schema_file = self.schemas_dir / "evaluation_schema.json"
            if not schema_file.exists():
                raise FileNotFoundError(f"評価用スキーマファイルが見つかりません: {schema_file}")
            with open(schema_file, "r", encoding="utf-8") as f:
                self._evaluation_schema = json.load(f)
        return self._evaluation_schema

    def get_evaluation_columns(self, df: pd.DataFrame, include_optional: bool = True) -> List[str]:
        """
        評価用カラムを取得（evaluation_schema.jsonに基づく）。
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            include_optional: オプションカラムを含めるか（デフォルト: True）
            
        Returns:
            評価用カラムのリスト（日本語キー）
        """
        schema = self.load_evaluation_schema()
        evaluation_cols = []
        
        # スキーマから評価用カラムを取得
        for col_def in schema.get("columns", []):
            col_name = col_def.get("name")
            if col_name and col_name in df.columns:
                required = col_def.get("required", False)
                category = col_def.get("category", "optional")
                
                # 必須カラムは常に含める
                if required or category == "merge_key":
                    evaluation_cols.append(col_name)
                # オプションカラムはinclude_optionalがTrueの場合のみ含める
                elif include_optional and category == "optional":
                    evaluation_cols.append(col_name)
        
        return evaluation_cols

    def get_evaluation_columns_by_metrics(self, df: pd.DataFrame, metrics: List[str]) -> List[str]:
        """
        指定された評価指標に必要なカラムを取得。
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            metrics: 評価指標のリスト（例: ["ndcg", "hit_rate", "return_rate_single", "win5_accuracy"]）
            
        Returns:
            評価指標に必要なカラムのリスト（日本語キー）
        """
        schema = self.load_evaluation_schema()
        required_cols = set()
        
        # マージキーは常に含める
        merge_keys = schema.get("merge_keys", {}).get("keys", [])
        required_cols.update(merge_keys)
        
        # 各評価指標に必要なカラムを取得
        evaluation_metrics = schema.get("evaluation_metrics", {})
        for metric in metrics:
            if metric in evaluation_metrics:
                metric_cols = evaluation_metrics[metric].get("required_columns", [])
                required_cols.update(metric_cols)
        
        # 必須カラムも含める
        for col_def in schema.get("columns", []):
            if col_def.get("required", False):
                col_name = col_def.get("name")
                if col_name and col_name in df.columns:
                    required_cols.add(col_name)
        
        # DataFrameに存在するカラムのみを返す
        return [col for col in required_cols if col in df.columns]

