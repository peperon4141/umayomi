"""カラム選択処理"""

from pathlib import Path
from typing import List, Tuple

import pandas as pd

from .column_filter import ColumnFilter


class ColumnSelector:
    """学習用・評価用カラムを選択するクラス"""

    def __init__(self, base_path: Path):
        """初期化。base_path: プロジェクトのベースパス"""
        self._column_filter = ColumnFilter(base_path)

    def select_training(self, df: pd.DataFrame) -> pd.DataFrame:
        """学習用カラムを選択。df: 変換済みDataFrame（英語キー）。学習用カラムのみのDataFrameを返す"""
        return self._column_filter.filter_training_columns(df)

    def select_evaluation(self, df: pd.DataFrame) -> pd.DataFrame:
        """評価用カラムを選択（日本語キーの全カラム）。df: 結合済みDataFrame（日本語キー）。評価用カラムのみのDataFrameを返す"""
        jp_cols = self._column_filter.get_all_japanese_columns(df)
        if jp_cols:
            return df[jp_cols].copy()
        return df.copy()

