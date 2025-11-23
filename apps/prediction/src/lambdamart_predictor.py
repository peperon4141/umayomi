"""
LambdaMART Predictor - LambdaMARTを使用したランキング学習モデル
LambdaMARTはLambdaRankの改良版で、勾配ブースティングを使用
"""

from functools import cached_property
from typing import Dict, Optional

import lightgbm as lgb
import numpy as np
import optuna.integration.lightgbm as optunaLgb
import pandas as pd

from .base_predictor import BasePredictor


class LambdaMARTPredictor(BasePredictor):
    """
    LambdaMARTを使用したランキング学習モデル
    レース内での相対的な順位を予測

    LambdaMARTの特徴:
    - LambdaRankの改良版
    - 勾配ブースティングを使用
    - より複雑なパターンを学習可能

    注意: パラメータはLambdaRankと同程度に設定されており、
    的中率改善のため、過度な正則化や制限は避けています。
    """

    @cached_property
    def common_params(self) -> dict:
        """LambdaMART用の共通パラメータ（的中率改善のため調整）"""
        import os

        num_threads = int(os.getenv("LIGHTGBM_NUM_THREADS", os.cpu_count() or 4))

        return {
            "objective": "lambdarank",  # LambdaMART（LightGBMではlambdarankがLambdaMARTを実装）
            "metric": "ndcg",
            "ndcg_eval_at": [1, 2, 3],
            "boosting_type": "gbdt",
            "random_state": 0,
            # LambdaMART用の最適化パラメータ（的中率改善のため調整）
            "num_leaves": 31,  # LambdaRankと同程度（表現力を確保）
            "max_depth": -1,  # 制限なし（num_leavesで制御）
            "learning_rate": 0.1,  # LambdaRankと同程度（学習を促進）
            "min_data_in_leaf": 20,  # LambdaRankと同程度（過学習防止）
            "min_gain_to_split": 0.0,  # 分割の最小ゲイン
            "lambda_l1": 0.0,  # 正則化なし（LambdaRankと同様）
            "lambda_l2": 0.0,  # 正則化なし（LambdaRankと同様）
            "feature_fraction": 1.0,  # 全特徴量を使用（LambdaRankと同様）
            "bagging_fraction": 1.0,  # 全データを使用（LambdaRankと同様）
            "bagging_freq": 0,  # バギングなし（LambdaRankと同様）
            "deterministic": True,
            "force_row_wise": True,
            "num_threads": num_threads,
            "max_bin": 255,
            "verbose": -1,
        }

    @cached_property
    def best_params(self) -> dict:
        """最適パラメータ（Optunaでチューニングされる）"""
        return {**self.common_params}

    @cached_property
    def lgb_train(self) -> lgb.Dataset:
        """学習用LightGBMデータセット"""
        return self._generate_dataset(self.train_df)

    @cached_property
    def lgb_val(self) -> lgb.Dataset:
        """検証用LightGBMデータセット"""
        return self._generate_dataset(self.val_df, self.lgb_train)

    def _convert_to_rank(self, rank: int) -> int:
        """
        着順をランキング学習用のスコアに変換
        1着=3, 2着=2, 3着=1, その他=0
        """
        if rank == 1:
            return 3
        if rank == 2:
            return 2
        if rank == 3:
            return 1
        return 0

    def _generate_dataset(
        self, df: pd.DataFrame, reference: Optional[lgb.Dataset] = None
    ) -> lgb.Dataset:
        """
        LightGBMデータセットを生成

        Args:
            df: DataFrame
            reference: 参照データセット（検証データ用）

        Returns:
            LightGBMデータセット
        """
        # ターゲット（着順）を変換
        if "rank" not in df.columns:
            raise ValueError("'rank'列がDataFrameに存在しません")

        target = list(map(self._convert_to_rank, df["rank"].values))

        # グループ情報（レース単位）
        if df.index.name == "race_key":
            group_sizes = df.groupby(df.index).size().tolist()
        elif "race_key" in df.columns:
            group_sizes = df.groupby("race_key").size().tolist()
        else:
            raise ValueError("レースキー（race_key）が見つかりません")

        # 特徴量の存在確認
        available_features = [f for f in self.encoded_feature_names if f in df.columns]

        # object型のカラムを除外（LightGBMは数値型のみ受け付ける）
        # course_type（文字列）は除外し、e_course_type（数値）を使用
        features_for_lgb = []
        for feat in available_features:
            if feat in df.columns:
                dtype = df[feat].dtype
                if dtype != "object" and str(dtype) != "object":
                    features_for_lgb.append(feat)

        if not features_for_lgb:
            raise ValueError(f"特徴量が見つかりません。利用可能な列: {df.columns.tolist()[:10]}")

        return lgb.Dataset(
            df[features_for_lgb], label=target, group=group_sizes, reference=reference
        )

    def train(
        self,
        early_stopping_rounds: int = 50,
        num_boost_round: int = 1000,  # LambdaRankと同程度
        optuna_timeout: Optional[int] = None,
        optuna_n_trials: Optional[int] = 100,  # より多くの試行で最適化（的中率改善）
    ) -> lgb.Booster:
        """
        LambdaMARTモデルを学習

        Args:
            early_stopping_rounds: 早期停止のラウンド数
            num_boost_round: 最大ブーストラウンド数
            optuna_timeout: Optunaの最大実行時間（秒）
            optuna_n_trials: Optunaの最大試行回数

        Returns:
            学習済みLightGBMモデル
        """
        # early_stopping_roundsはparamsに含める必要がある
        params_with_early_stopping = self.best_params.copy()
        params_with_early_stopping["early_stopping_rounds"] = early_stopping_rounds

        optuna_kwargs = {
            "optuna_seed": 123,
        }

        if optuna_timeout is not None:
            optuna_kwargs["time_budget"] = optuna_timeout

        booster = optunaLgb.LightGBMTuner(
            params=params_with_early_stopping,
            train_set=self.lgb_train,
            valid_sets=[self.lgb_train, self.lgb_val],
            valid_names=["train", "val"],
            num_boost_round=num_boost_round,
            **optuna_kwargs,
        )
        booster.run()
        print("最適パラメータ:", booster.best_params)
        return booster.get_best_booster()

    @staticmethod
    def predict(model: lgb.Booster, race_df: pd.DataFrame, features: Features) -> pd.DataFrame:
        """
        予測を実行

        Args:
            model: 学習済みLightGBMモデル
            race_df: 予測対象のDataFrame
            features: Featuresインスタンス

        Returns:
            予測結果が追加されたDataFrame
        """
        # race_keyがインデックスとカラムの両方に存在する場合の処理
        race_df_processed = race_df.copy()

        if race_df_processed.index.name == "race_key":
            if "race_key" in race_df_processed.columns:
                race_df_processed = race_df_processed.drop(columns=["race_key"])
            race_df_processed = race_df_processed.reset_index()
        elif (
            race_df_processed.index.name != "race_key"
            and "race_key" not in race_df_processed.columns
        ):
            raise ValueError("race_keyがインデックスにもカラムにも存在しません")

        available_features = [
            f for f in features.encoded_feature_names if f in race_df_processed.columns
        ]

        if not available_features:
            raise ValueError(
                f"特徴量が見つかりません。利用可能な列: {race_df_processed.columns.tolist()[:10]}"
            )

        predictions = model.predict(
            race_df_processed[available_features], num_iteration=model.best_iteration
        )

        result_df = race_df_processed.copy()
        result_df.insert(0, "predict", np.round(predictions, 2))

        # 根本解決: race_keyと馬番の型を統一（odds_dfとのマージを確実にするため）
        if "race_key" in result_df.columns:
            result_df["race_key"] = result_df["race_key"].astype(str)
        if "馬番" in result_df.columns:
            result_df["馬番"] = pd.to_numeric(result_df["馬番"], errors="coerce")

        return result_df

    @staticmethod
