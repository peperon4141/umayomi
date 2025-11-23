"""特徴量抽出処理（前走データと統計特徴量）"""

from typing import Dict, Optional

import pandas as pd

from . import previous_race_extractor, statistical_feature_calculator


class FeatureExtractor:
    """特徴量を抽出するクラス（前走データと統計特徴量）"""

    def extract_previous_races(
        self, df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """前走データを抽出。df: 結合済みDataFrame、sed_df: SEDデータ、bac_df: BACデータ（オプション）。前走データが追加されたDataFrameを返す"""
        return previous_race_extractor.extract(df, sed_df, bac_df)

    def extract_statistics(
        self, df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """統計特徴量を計算。df: 結合済みDataFrame、sed_df: SEDデータ、bac_df: BACデータ（オプション）。統計特徴量が追加されたDataFrameを返す"""
        return statistical_feature_calculator.calculate(df, sed_df, bac_df)

