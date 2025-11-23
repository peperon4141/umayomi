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
            学習用カラムが選択されたDataFrame（ターゲット変数を含む）
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
        
        return df[available_columns].copy()

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

    def get_evaluation_columns(self, df: pd.DataFrame) -> List[str]:
        """
        評価用カラムを取得（full_info_schema.jsonの全カラムから、use_for_training=falseのカラム + rank, time）。
        df: 結合済みDataFrame（英語キーに変換済み）
        """
        schema = self.load_full_info_schema()
        training_columns = self.get_training_columns()
        evaluation_cols = []
        
        # full_info_schema.jsonから評価用カラムを取得
        for col in schema.get("columns", []):
            feature_name = col.get("feature_name")
            if feature_name and feature_name in df.columns:
                # use_for_training=falseのカラム、またはrank/timeは評価用
                if not col.get("use_for_training", False) or feature_name in ["rank", "time"]:
                    evaluation_cols.append(feature_name)
        
        # rankとtimeは必ず含める
        if "rank" in df.columns and "rank" not in evaluation_cols:
            evaluation_cols.append("rank")
        if "time" in df.columns and "time" not in evaluation_cols:
            evaluation_cols.append("time")
        
        return evaluation_cols

