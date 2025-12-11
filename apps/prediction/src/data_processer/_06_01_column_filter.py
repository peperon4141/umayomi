"""学習用データの必要なカラムを選択し、評価用カラムを識別する"""

import logging
from typing import List, Set, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from src.utils.schema_loader import Schema

logger = logging.getLogger(__name__)


class ColumnFilter:
    """学習用データの必要なカラムを選択するクラス（staticメソッドのみ）"""

    @staticmethod
    def get_training_columns(full_info_schema: "Schema") -> Set[str]:
        """学習用データの必要なカラム名のセットを取得（英語キー、use_for_training=trueのカラム）"""
        from src.utils.schema_loader import Column
        # use_for_training=trueのカラムのfeature_nameを取得
        training_columns = set()
        columns = full_info_schema.columns
        for col in columns:
            if isinstance(col, Column):
                use_for_training = getattr(col, "use_for_training", False)
                feature_name = col.feature_name
            else:
                use_for_training = col.get("use_for_training", False)
                feature_name = col.get("feature_name")
            if use_for_training and feature_name:
                training_columns.add(feature_name)
        # rank（ターゲット変数）も追加
        training_columns.add("rank")
        return training_columns

    @staticmethod
    def filter_training_columns(df: pd.DataFrame, full_info_schema: "Schema", training_schema: "Schema") -> pd.DataFrame:
        """
        学習用データの必要なカラムを選択。
        
        Args:
            df: 対象のDataFrame
            
        Returns:
            学習用カラムが選択されたDataFrame（ターゲット変数を含む、インデックス名も保持）
        """
        training_columns = ColumnFilter.get_training_columns(full_info_schema)  # これでtarget_variableも含まれる
        available_columns = [col for col in training_columns if col in df.columns]
        missing_columns = training_columns - set(df.columns)
        
        # ターゲット変数が欠けている場合はエラー
        target_variable = training_schema.target_variable
        if target_variable is None:
            raise ValueError("training_schemaにtarget_variableが定義されていません。スキーマファイルを確認してください。")
        target_name = target_variable.get("name") if isinstance(target_variable, dict) else getattr(target_variable, "name", None)
        if not target_name:
            raise ValueError("training_schemaのtarget_variableにnameが定義されていません。スキーマファイルを確認してください。")
        if target_name not in df.columns:
            raise ValueError(f"ターゲット変数 '{target_name}' がDataFrameに存在しません。学習時に必須です。")
        
        if missing_columns:
            logger.warning(f"学習用スキーマに定義されているが、データに存在しないカラム: {sorted(missing_columns)}")
        
        # カラムを選択し、インデックス名を保持
        result = df[available_columns].copy()
        result.index.name = df.index.name  # インデックス名を明示的に保持
        return result

    @staticmethod
    def get_all_columns(df: pd.DataFrame, full_info_schema: "Schema") -> List[str]:
        """full_info_schema.jsonの全カラム（英語キー）を取得"""
        from src.utils.schema_loader import Column
        all_cols = []
        columns = full_info_schema.columns
        for col in columns:
            if isinstance(col, Column):
                feature_name = col.feature_name
            else:
                feature_name = col.get("feature_name")
            if feature_name and feature_name in df.columns:
                all_cols.append(feature_name)
        return all_cols

    @staticmethod
    def get_all_japanese_columns(df: pd.DataFrame, full_info_schema: "Schema") -> List[str]:
        """full_info_schema.jsonの全カラム（日本語キー）を取得"""
        from src.utils.schema_loader import Column
        all_cols = []
        columns = full_info_schema.columns
        for col in columns:
            if isinstance(col, Column):
                jp_name = col.name
            else:
                jp_name = col.get("name")
            if jp_name and jp_name in df.columns:
                all_cols.append(jp_name)
        return all_cols

    @staticmethod
    def get_evaluation_columns(df: pd.DataFrame, evaluation_schema: "Schema", include_optional: bool = True) -> List[str]:
        """
        評価用カラムを取得（evaluation_schema.jsonに基づく）。
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            include_optional: オプションカラムを含めるか（デフォルト: True）
            
        Returns:
            評価用カラムのリスト（日本語キー）
        """
        from src.utils.schema_loader import Column
        evaluation_cols = []
        columns = evaluation_schema.columns
        
        # スキーマから評価用カラムを取得
        for col_def in columns:
            if isinstance(col_def, Column):
                col_name = col_def.name
                required = getattr(col_def, "required", False)
                category = getattr(col_def, "category", "optional")
            else:
                col_name = col_def.get("name")
                required = col_def.get("required", False)
                category = col_def.get("category", "optional")
            if col_name and col_name in df.columns:
                # 必須カラムは常に含める
                if required or category == "merge_key":
                    evaluation_cols.append(col_name)
                # オプションカラムはinclude_optionalがTrueの場合のみ含める
                elif include_optional and category == "optional":
                    evaluation_cols.append(col_name)
        
        return evaluation_cols

    @staticmethod
    def get_evaluation_columns_by_metrics(df: pd.DataFrame, evaluation_schema: "Schema", metrics: List[str]) -> List[str]:
        """
        指定された評価指標に必要なカラムを取得。
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            metrics: 評価指標のリスト（例: ["ndcg", "hit_rate", "return_rate_single", "win5_accuracy"]）
            
        Returns:
            評価指標に必要なカラムのリスト（日本語キー）
        """
        from src.utils.schema_loader import Column
        required_cols = set()
        
        # マージキーは常に含める
        if evaluation_schema.merge_keys and isinstance(evaluation_schema.merge_keys, dict):
            required_cols.update(evaluation_schema.merge_keys.get("keys", []))
        
        # 各評価指標に必要なカラムを取得
        if evaluation_schema.evaluation_metrics and isinstance(evaluation_schema.evaluation_metrics, dict):
            for metric in metrics:
                if metric in evaluation_schema.evaluation_metrics:
                    metric_cols = evaluation_schema.evaluation_metrics[metric].get("required_columns", [])
                    required_cols.update(metric_cols)
        
        # 必須カラムも含める
        for col_def in evaluation_schema.columns:
            if isinstance(col_def, Column):
                required = getattr(col_def, "required", False)
                col_name = col_def.name
            else:
                required = col_def.get("required", False)
                col_name = col_def.get("name")
            if required and col_name and col_name in df.columns:
                required_cols.add(col_name)
        
        # DataFrameに存在するカラムのみを返す
        return [col for col in required_cols if col in df.columns]
