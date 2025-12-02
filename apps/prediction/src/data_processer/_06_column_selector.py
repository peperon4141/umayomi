"""カラム選択処理"""

from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from ._06_01_column_filter import ColumnFilter


class ColumnSelector:
    """学習用・評価用カラムを選択するクラス"""

    def __init__(self, base_path: Path):
        """初期化。base_path: プロジェクトのベースパス"""
        self._column_filter = ColumnFilter(base_path)

    def select_training(self, df: pd.DataFrame) -> pd.DataFrame:
        """学習用カラムを選択。df: 変換済みDataFrame（英語キー）。学習用カラムのみのDataFrameを返す"""
        return self._column_filter.filter_training_columns(df)

    def select_evaluation(
        self, df: pd.DataFrame, include_optional: bool = True, metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        評価用カラムを選択（evaluation_schema.jsonに基づく）。
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            include_optional: オプションカラムを含めるか（デフォルト: True）
            metrics: 評価指標のリスト（指定された場合、その指標に必要なカラムのみを選択）
            
        Returns:
            評価用カラムのみのDataFrame（日本語キー）
        """
        if metrics:
            eval_cols = self._column_filter.get_evaluation_columns_by_metrics(df, metrics)
        else:
            eval_cols = self._column_filter.get_evaluation_columns(df, include_optional=include_optional)
        
        if eval_cols:
            return df[eval_cols].copy()
        return df.copy()

