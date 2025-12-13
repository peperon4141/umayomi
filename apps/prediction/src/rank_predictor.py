"""
RankPredictor - LambdaRankを使用したランキング学習モデル
"""

from functools import cached_property
from typing import Dict, Optional

import lightgbm as lgb
import numpy as np
import optuna.integration.lightgbm as optunaLgb
import pandas as pd

from .base_predictor import BasePredictor
from .features import Features


class RankPredictor(BasePredictor):
    """
    LambdaRankを使用したランキング学習モデル
    レース内での相対的な順位を予測
    """

    @cached_property
    def common_params(self) -> dict:
        """共通パラメータ（効率化のための最適化済み）"""
        import os

        # CPUスレッド数を取得（環境変数で指定されていない場合）
        num_threads = int(os.getenv("LIGHTGBM_NUM_THREADS", os.cpu_count() or 4))

        return {
            "objective": "lambdarank",
            "metric": "ndcg",
            "ndcg_eval_at": [1, 2, 3],
            "boosting_type": "gbdt",
            "random_state": 0,
            "num_leaves": 127,  # 的中率向上のため増加（31→127）
            "learning_rate": 0.05,  # 学習率を調整
            "min_data_in_leaf": 10,  # 的中率向上のため削減（20→10）
            "max_depth": 10,  # 深さを制限して過学習防止
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

        # NaN値を除外してから変換
        rank_values = df["rank"].values
        # NaNを0に変換（着順不明の場合は0点）
        rank_values = np.nan_to_num(rank_values, nan=0.0).astype(int)
        target = list(map(self._convert_to_rank, rank_values))

        # グループ情報（レース単位）
        if df.index.name == "race_key":
            # インデックスがrace_keyの場合
            # インデックスでグループ化（level=0を使用）
            group_sizes = df.groupby(level=0).size().tolist()
        elif "race_key" in df.columns:
            # race_key列がある場合
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
        num_boost_round: int = 1000,
        optuna_timeout: Optional[int] = None,
        optuna_n_trials: Optional[int] = 150,  # 的中率向上のため試行回数を増加（50→150）
    ) -> lgb.Booster:
        """
        モデルを学習（効率化のための最適化済み）

        Args:
            early_stopping_rounds: 早期停止のラウンド数（検証データの改善が止まったら学習を停止）
            num_boost_round: 最大ブーストラウンド数
            optuna_timeout: Optunaの最大実行時間（秒）。Noneの場合は制限なし
            optuna_n_trials: Optunaの最大試行回数。Noneの場合はデフォルト値を使用

        Returns:
            学習済みLightGBMモデル
        """
        # Optunaの設定
        # early_stopping_roundsはparamsに含める必要がある
        params_with_early_stopping = self.best_params.copy()
        params_with_early_stopping["early_stopping_rounds"] = early_stopping_rounds

        optuna_kwargs = {
            "optuna_seed": 123,  # 再現性確保用のパラメータ
        }

        # time_budgetは秒単位で指定（timeoutの代わり）
        if optuna_timeout is not None:
            optuna_kwargs["time_budget"] = optuna_timeout

        # n_trialsはLightGBMTunerでは直接サポートされていないため、
        # time_budgetで制御するか、studyオブジェクトを使用する必要がある
        # 現時点ではtime_budgetのみを使用

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
            race_keyとpredict列のみを含むDataFrame
        """
        race_df_processed = race_df.copy()
        
        if race_df_processed.index.name == "race_key":
            if "race_key" in race_df_processed.columns:
                race_df_processed = race_df_processed.drop(columns=["race_key"])
            race_df_processed = race_df_processed.reset_index()
        elif "race_key" not in race_df_processed.columns:
            raise ValueError("race_keyがインデックスにもカラムにも存在しません")

        # モデルが期待する特徴量名を取得（モデルに保存されている特徴量名を使用）
        model_feature_names = model.feature_name()
        if model_feature_names:
            # モデルが期待する特徴量のみを使用（学習時と同じ特徴量を使用）
            features_for_lgb = [f for f in model_feature_names if f in race_df_processed.columns and race_df_processed[f].dtype != "object"]
        else:
            # モデルに特徴量名が保存されていない場合、Featuresクラスから取得
            available_features = [f for f in features.encoded_feature_names if f in race_df_processed.columns]
            features_for_lgb = [f for f in available_features if race_df_processed[f].dtype != "object"]

        if not features_for_lgb:
            raise ValueError(f"特徴量が見つかりません。利用可能な列: {race_df_processed.columns.tolist()[:10]}")

        # 不足している特徴量を0で補完（学習時と予測時で特徴量が異なる場合）
        for feat in model_feature_names if model_feature_names else []:
            if feat not in race_df_processed.columns:
                race_df_processed[feat] = 0.0
                if feat not in features_for_lgb:
                    features_for_lgb.append(feat)

        # 予測実行（numpy配列に変換して予測）
        # LightGBMの予測では、Pandas DataFrameを直接使用するとカテゴリカル特徴量の不一致エラーが発生する場合がある
        # そのため、numpy配列に変換して予測することで回避
        # また、predict_disable_shape_check=Trueを指定して特徴量数の不一致を回避
        try:
            predictions = model.predict(
                race_df_processed[features_for_lgb].values, 
                num_iteration=model.best_iteration,
                predict_disable_shape_check=True
            )
        except Exception as e:
            # エラーが発生した場合、型変換を試みる
            import warnings
            warnings.warn(f"予測エラーが発生しました。型変換を試みます: {e}")
            # 数値型に変換できるカラムを数値型に変換
            race_df_numeric = race_df_processed[features_for_lgb].copy()
            for col in features_for_lgb:
                if race_df_numeric[col].dtype == "object":
                    try:
                        race_df_numeric[col] = pd.to_numeric(race_df_numeric[col], errors='coerce').fillna(0)
                    except:
                        race_df_numeric[col] = 0
            predictions = model.predict(
                race_df_numeric.values, 
                num_iteration=model.best_iteration,
                predict_disable_shape_check=True
            )
        
        return pd.DataFrame({
            "race_key": race_df_processed["race_key"].values,
            "predict": np.round(predictions, 2)
        })

    def get_result(self, model: lgb.Booster, race_df: pd.DataFrame, rank_in: int = 1) -> tuple:
        """
        予測結果を取得（評価用）

        Args:
            model: 学習済みLightGBMモデル
            race_df: 予測対象のDataFrame
            rank_in: 評価対象の着順範囲

        Returns:
            (bet, success, gain, sorted_race_df) のタプル
        """
        available_features = [f for f in self.encoded_feature_names if f in race_df.columns]

        predictions = model.predict(race_df[available_features], num_iteration=model.best_iteration)

        result_df = race_df.copy()
        result_df.insert(0, "predicted_score", np.round(predictions, 2))
        sorted_race_df = result_df.sort_values("predicted_score", ascending=False)

        # predicted_scoreの値が大きい順に、predicted_rank列を追加
        sorted_race_df.insert(1, "predicted_rank", range(1, len(sorted_race_df) + 1))

        bet = True
        success = False
        gain = 0

        if "rank" in sorted_race_df.columns:
            ranks = sorted_race_df["rank"].tolist()[0:rank_in]
            if bet and 1 in ranks:
                success = True
                # オッズは別途計算するため、ここでは0を返す
                gain = 0

        return bet, success, gain, sorted_race_df
