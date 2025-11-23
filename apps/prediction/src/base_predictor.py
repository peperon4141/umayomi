"""
基底予測クラス
各予測モデルの共通機能を提供
"""

from functools import cached_property
from typing import Dict, Optional

import pandas as pd

from .evaluator import evaluate_model, print_evaluation_results
from .features import Features


class BasePredictor:
    """
    予測モデルの基底クラス
    共通機能を提供
    """

    def __init__(self, train_df: pd.DataFrame, val_df: pd.DataFrame):
        """
        初期化

        Args:
            train_df: 学習用DataFrame
            val_df: 検証用DataFrame
        """
        self.features = Features()
        self.train_df = train_df
        self.val_df = val_df

    @cached_property
    def feature_names(self) -> list:
        """特徴量名のリスト"""
        return self.features.feature_names

    @cached_property
    def encoded_feature_names(self) -> list:
        """エンコード済み特徴量名のリスト"""
        return self.features.encoded_feature_names

    def evaluate(self, predictions_df: pd.DataFrame, odds_col: Optional[str] = None) -> Dict[str, float]:
        """
        モデル評価を実行

        Args:
            predictions_df: 予測結果のDataFrame（race_key, rank, predict, 馬番を含む）
            odds_col: 確定単勝オッズのカラム名（オプション、回収率計算用）

        Returns:
            評価結果の辞書
        """
        return evaluate_model(predictions_df, odds_col=odds_col)

    @staticmethod
    def print_evaluation(predictions_df: pd.DataFrame, odds_col: Optional[str] = None) -> None:
        """
        モデル評価を実行して結果を表示

        Args:
            predictions_df: 予測結果のDataFrame（race_key, rank, predict, 馬番を含む）
            odds_col: 確定単勝オッズのカラム名（オプション、回収率計算用）
        """
        results = evaluate_model(predictions_df, odds_col=odds_col)
        print_evaluation_results(results)

