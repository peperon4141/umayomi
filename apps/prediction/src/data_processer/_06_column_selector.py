"""カラム選択処理"""

from typing import List, Optional, TYPE_CHECKING

import pandas as pd

from ._06_01_column_filter import ColumnFilter

if TYPE_CHECKING:
    from src.utils.schema_loader import Schema


class ColumnSelector:
    """学習用・評価用カラムを選択するクラス（staticメソッドのみ）"""

    @staticmethod
    def select_training(df: pd.DataFrame, full_info_schema: "Schema", training_schema: "Schema") -> pd.DataFrame:
        """
        学習用カラムを選択
        
        Args:
            df: 変換済みDataFrame（英語キー）
            full_info_schema: full_info_schema.jsonの内容
            training_schema: training_schema.jsonの内容
        
        Returns:
            学習用カラムのみのDataFrame
        """
        return ColumnFilter.filter_training_columns(df, full_info_schema, training_schema)

    @staticmethod
    def select_evaluation(
        df: pd.DataFrame, evaluation_schema: "Schema", include_optional: bool = True, metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        評価用カラムを選択（evaluation_schema.jsonに基づく）。
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            evaluation_schema: evaluation_schema.jsonの内容
            include_optional: オプションカラムを含めるか（デフォルト: True）
            metrics: 評価指標のリスト（指定された場合、その指標に必要なカラムのみを選択）
            
        Returns:
            評価用カラムのみのDataFrame（日本語キー）
        """
        if metrics:
            eval_cols = ColumnFilter.get_evaluation_columns_by_metrics(df, evaluation_schema, metrics)
        else:
            eval_cols = ColumnFilter.get_evaluation_columns(df, evaluation_schema, include_optional=include_optional)
        
        if eval_cols:
            return df[eval_cols].copy()
        return df.copy()

