"""
ComplementaryPredictor - 相互補完学習による競馬予想モデル

着順予測と走破タイム予測を相互に補完し合うことで精度を向上させる手法

タスク1: 着順予測（ランキング学習）
タスク2: 走破タイム予測（回帰）

事実ベースの特徴量のみを使用:
- JRDBの事前予想は除外
- オッズは除外
"""

from functools import cached_property
from typing import List, Optional

import lightgbm as lgb
import numpy as np
import pandas as pd

from .features import Features


class ComplementaryPredictor:
    """
    相互補完学習による競馬予想モデル

    着順予測と走破タイム予測を独立して学習し、
    相互に予測結果を特徴量として追加して再学習することで精度を向上させる

    タスク1: 着順予測（ランキング学習）
    タスク2: 走破タイム予測（回帰）
    """

    def __init__(self, train_df: pd.DataFrame, val_df: pd.DataFrame):
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

    def _calculate_standard_time_per_100m(
        self, course_type: pd.Series, ground_condition: pd.Series
    ) -> pd.Series:
        """
        標準タイム（秒/100m）を計算

        距離・コース条件・馬場状態を考慮した標準タイム
        """
        # 基本タイム（芝・良馬場）
        base_time = 6.0

        # コースタイプによる調整
        course_factor = course_type.map(
            {"芝": 1.0, "ダ": 1.05, "ダート": 1.05, "障": 1.10, "障害": 1.10}
        ).fillna(1.0)

        # 馬場状態による調整
        ground_factor = ground_condition.map(
            {"良": 1.0, "稍": 1.02, "重": 1.05, "不": 1.08, "重不": 1.10}
        ).fillna(1.0)

        return base_time * course_factor * ground_factor

    def _normalize_time(
        self,
        time: pd.Series,
        distance: pd.Series,
        course_type: pd.Series,
        ground_condition: pd.Series,
    ) -> pd.Series:
        """
        タイムを正規化（標準タイムとの比較）

        1.0 = 標準タイム
        0.95 = 標準より5%速い
        1.05 = 標準より5%遅い
        """
        # 距離による正規化（秒/100m）
        time_per_100m = time / (distance / 100)

        # 標準タイム（秒/100m）
        standard_time_per_100m = self._calculate_standard_time_per_100m(
            course_type, ground_condition
        )

        # 正規化タイム（標準タイムとの比率）
        # ゼロ除算を防ぐ
        normalized_time = time_per_100m / standard_time_per_100m.replace(0, np.nan)

        return normalized_time

    def _calculate_race_pace_score(self, race_df: pd.DataFrame) -> pd.Series:
        """
        レース全体のペーススコアを計算（事実ベース）

        脚質の分布からペースを予測（JRDBのペース予想は使用しない）
        """
        pace_scores = []

        for race_key in race_df.index.unique():
            if isinstance(race_df.index, pd.MultiIndex):
                race_data = race_df.loc[race_key]
            else:
                race_data = race_df[race_df.index == race_key]

            if isinstance(race_data, pd.Series):
                race_data = race_data.to_frame().T

            # 脚質の分布
            if "running_style" in race_data.columns:
                running_styles = race_data["running_style"].value_counts()

                # 逃げ・先行馬の割合
                front_runners = running_styles.get("逃げ", 0) + running_styles.get("先行", 0)
                total_horses = len(race_data)

                # ペーススコア（0.0-1.0）
                pace_score = front_runners / total_horses if total_horses > 0 else 0.5

                # 距離による調整（短距離はハイペースになりやすい）
                if "course_length" in race_data.columns:
                    distance = (
                        race_data["course_length"].iloc[0]
                        if hasattr(race_data, "iloc")
                        else race_data["course_length"].values[0]
                    )
                    if distance < 1400:
                        pace_score = min(pace_score * 1.2, 1.0)
                    elif distance > 2400:
                        pace_score = max(pace_score * 0.8, 0.0)
            else:
                pace_score = 0.5  # デフォルト
                total_horses = len(race_data)

            # レース内の全馬に同じペーススコアを割り当て
            pace_scores.extend([pace_score] * total_horses)

        return pd.Series(pace_scores, index=race_df.index)

    def _generate_time_dataset(
        self, df: pd.DataFrame, reference: Optional[lgb.Dataset] = None
    ) -> lgb.Dataset:
        """
        走破タイム予測用のデータセットを生成

        ターゲット: 正規化された走破タイム
        """
        # SEDデータからタイムを取得
        if "タイム" not in df.columns:
            raise ValueError("'タイム'列がDataFrameに存在しません")

        # 必要なカラムの存在確認と補完
        # course_typeの補完（文字列として）
        if "course_type" not in df.columns:
            if "芝ダ障害コード" in df.columns:
                course_type_map = {"1": "芝", "2": "ダ", "3": "障"}
                df["course_type"] = (
                    df["芝ダ障害コード"].astype(str).map(course_type_map).fillna("芝")
                )
            else:
                # デフォルト値
                df["course_type"] = "芝"

        # ground_conditionの補完（文字列として）
        if "ground_condition" not in df.columns:
            if "馬場状態" in df.columns:
                df["ground_condition"] = df["馬場状態"]
            else:
                # デフォルト値
                df["ground_condition"] = "良"

        # course_lengthの補完
        if "course_length" not in df.columns:
            if "距離" in df.columns:
                df["course_length"] = df["距離"]
            else:
                raise ValueError(
                    f"course_length（距離）カラムが見つかりません\n"
                    f"利用可能なカラム: {sorted(df.columns.tolist())[:30]}..."
                )

        # タイムを正規化（文字列のcourse_typeとground_conditionを使用）
        normalized_time = self._normalize_time(
            df["タイム"], df["course_length"], df["course_type"], df["ground_condition"]
        )

        # ペーススコアを計算（事実ベース）
        race_pace_score = self._calculate_race_pace_score(df)

        # 特徴量にペーススコアを追加
        df_with_pace = df.copy()
        df_with_pace["race_pace_score"] = race_pace_score

        # タイム正規化用に追加したobject型カラムを削除（LightGBM用）
        # course_type, ground_conditionは文字列なので、e_*カラムを使用
        if "course_type" in df_with_pace.columns and df_with_pace["course_type"].dtype == "object":
            # e_course_typeが存在する場合は、course_typeを削除
            if "e_course_type" in df_with_pace.columns:
                df_with_pace = df_with_pace.drop(columns=["course_type"])
        if (
            "ground_condition" in df_with_pace.columns
            and df_with_pace["ground_condition"].dtype == "object"
        ):
            # e_ground_conditionが存在する場合は、ground_conditionを削除
            if "e_ground_condition" in df_with_pace.columns:
                df_with_pace = df_with_pace.drop(columns=["ground_condition"])

        # 脚質とペースの相互作用特徴量
        if "running_style" in df_with_pace.columns:
            style_factor = (
                df_with_pace["running_style"]
                .map({"逃げ": 1.0, "先行": 0.7, "中団": 0.3, "後方": 0.0})
                .fillna(0.5)
            )
            df_with_pace["pace_running_style_interaction"] = race_pace_score * style_factor
        else:
            df_with_pace["pace_running_style_interaction"] = race_pace_score * 0.5

        # 特徴量を取得（エンコード済みカラムのみを使用）
        # encoded_feature_namesにはcourse_typeとe_course_typeの両方が含まれる可能性がある
        # object型のカラムは除外し、e_*カラムのみを使用
        available_features = []
        for f in self.encoded_feature_names:
            if f in df_with_pace.columns:
                # object型のカラムは除外（e_*カラムを使用）
                if df_with_pace[f].dtype != "object":
                    available_features.append(f)
                # object型の場合は、対応するe_*カラムが存在するか確認
                elif f.startswith("e_"):
                    # 既にe_*カラムの場合は追加（ただしobject型でないことを確認）
                    if df_with_pace[f].dtype != "object":
                        available_features.append(f)

        # ペース関連の特徴量を追加
        available_features.extend(["race_pace_score", "pace_running_style_interaction"])

        # 最終的なフィルタリング（object型を完全に除外）
        features_for_lgb = []
        for feat in available_features:
            if feat in df_with_pace.columns:
                # object型のカラムは完全に除外
                dtype = df_with_pace[feat].dtype
                if dtype != "object" and str(dtype) != "object":
                    features_for_lgb.append(feat)

        # 使用した特徴量のリストを保存（予測時に使用）
        dataset = lgb.Dataset(
            df_with_pace[features_for_lgb], label=normalized_time, reference=reference
        )
        # 特徴量名を保存（予測時に同じ順序で使用するため）
        dataset.feature_names = features_for_lgb
        return dataset

    def _train_rank_model(self) -> lgb.Booster:
        """着順予測モデルを学習（ランキング学習）"""
        from .rank_predictor import RankPredictor

        predictor = RankPredictor(self.train_df, self.val_df)
        return predictor.train()

    def _train_time_model(self) -> lgb.Booster:
        """走破タイム予測モデルを学習（回帰）"""
        # タイムが存在するデータのみを使用
        train_df_with_time = self.train_df[self.train_df["タイム"].notna()].copy()
        val_df_with_time = self.val_df[self.val_df["タイム"].notna()].copy()

        if len(train_df_with_time) == 0:
            raise ValueError("タイムが存在する学習データがありません")
        if len(val_df_with_time) == 0:
            raise ValueError("タイムが存在する検証データがありません")

        train_data = self._generate_time_dataset(train_df_with_time)
        val_data = self._generate_time_dataset(val_df_with_time, train_data)

        # 使用した特徴量名を保存（予測時に同じ特徴量を使用するため）
        self._time_model_feature_names = (
            train_data.feature_names if hasattr(train_data, "feature_names") else None
        )

        import os

        num_threads = int(os.getenv("LIGHTGBM_NUM_THREADS", os.cpu_count() or 4))

        params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 64,
            "learning_rate": 0.05,
            "max_depth": 10,
            "min_data_in_leaf": 20,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "lambda_l1": 0.1,
            "lambda_l2": 0.1,
            "deterministic": True,
            "force_row_wise": True,
            "num_threads": num_threads,
            "max_bin": 255,
            "verbose": -1,
        }

        model = lgb.train(
            params,
            train_data,
            valid_sets=[train_data, val_data],
            valid_names=["train", "val"],
            num_boost_round=1000,
            callbacks=[lgb.early_stopping(50)],
        )

        return model

    def train(self) -> dict[str, lgb.Booster]:
        """
        相互補完学習を実行

        Returns:
            {'rank_model': 着順予測モデル, 'time_model': タイム予測モデル}
        """
        print("=" * 60)
        print("相互補完学習を開始")
        print("=" * 60)

        # タスク1: 着順予測
        print("\n[1/2] 着順予測モデルを学習中...")
        rank_model = self._train_rank_model()
        print("✓ 着順予測モデルの学習完了")

        # タスク2: 走破タイム予測
        print("\n[2/2] 走破タイム予測モデルを学習中...")
        time_model = self._train_time_model()
        print("✓ 走破タイム予測モデルの学習完了")

        # 相互に特徴量を追加して再学習
        print("\n相互補完学習を開始...")

        print("  - タイム予測を特徴量として追加した着順予測モデルを再学習...")
        rank_model_v2 = self._train_rank_model_with_time(time_model)

        print("  - 着順予測を特徴量として追加したタイム予測モデルを再学習...")
        time_model_v2 = self._train_time_model_with_rank(rank_model)

        print("\n" + "=" * 60)
        print("相互補完学習完了")
        print("=" * 60)

        return {
            "rank_model": rank_model_v2,  # 第2段階: タイム予測を含む着順予測モデル
            "time_model": time_model_v2,  # 第3段階: 着順予測を含むタイム予測モデル
            "time_model_stage1": time_model,  # 第1段階: タイム予測モデル（予測時に使用）
            "rank_model_stage1": rank_model,  # 第1段階: 着順予測モデル（予測時に使用）
        }

    def _train_rank_model_with_time(self, time_model: lgb.Booster) -> lgb.Booster:
        """タイム予測を特徴量として追加した着順予測モデル"""
        # タイム予測を特徴量として追加
        # 学習時に使用した特徴量名を取得
        feature_names = getattr(self, "_time_model_feature_names", None)

        train_df_with_time = self.train_df.copy()
        train_features = self._get_features_for_prediction(train_df_with_time, feature_names)
        train_df_with_time["predicted_time"] = time_model.predict(train_features)

        val_df_with_time = self.val_df.copy()
        val_features = self._get_features_for_prediction(val_df_with_time, feature_names)
        val_df_with_time["predicted_time"] = time_model.predict(val_features)

        # 着順予測モデルを再学習
        from .rank_predictor import RankPredictor

        predictor = RankPredictor(train_df_with_time, val_df_with_time)
        return predictor.train()

    def _train_time_model_with_rank(self, rank_model: lgb.Booster) -> lgb.Booster:
        """着順予測を特徴量として追加したタイム予測モデル"""
        # タイムが存在するデータのみを使用
        train_df_with_rank = self.train_df[self.train_df["タイム"].notna()].copy()
        val_df_with_rank = self.val_df[self.val_df["タイム"].notna()].copy()

        if len(train_df_with_rank) == 0:
            raise ValueError("タイムが存在する学習データがありません")
        if len(val_df_with_rank) == 0:
            raise ValueError("タイムが存在する検証データがありません")

        # 着順予測を特徴量として追加
        # RankPredictorが使用する特徴量を取得（object型を除外）
        from .rank_predictor import RankPredictor

        rank_predictor = RankPredictor(train_df_with_rank, val_df_with_rank)
        rank_features = [
            f for f in rank_predictor.encoded_feature_names if f in train_df_with_rank.columns
        ]
        # object型を除外
        rank_features = [f for f in rank_features if train_df_with_rank[f].dtype != "object"]

        train_df_with_rank["predicted_rank"] = rank_model.predict(train_df_with_rank[rank_features])

        val_df_with_rank["predicted_rank"] = rank_model.predict(val_df_with_rank[rank_features])

        # タイム予測モデルを再学習
        train_data = self._generate_time_dataset_with_rank(train_df_with_rank)
        val_data = self._generate_time_dataset_with_rank(val_df_with_rank, train_data)

        # 使用した特徴量名を保存
        self._time_model_with_rank_feature_names = (
            train_data.feature_names if hasattr(train_data, "feature_names") else None
        )

        import os

        num_threads = int(os.getenv("LIGHTGBM_NUM_THREADS", os.cpu_count() or 4))

        params = {
            "objective": "regression",
            "metric": "rmse",
            "boosting_type": "gbdt",
            "num_leaves": 64,
            "learning_rate": 0.05,
            "max_depth": 10,
            "min_data_in_leaf": 20,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "lambda_l1": 0.1,
            "lambda_l2": 0.1,
            "deterministic": True,
            "force_row_wise": True,
            "num_threads": num_threads,
            "max_bin": 255,
            "verbose": -1,
        }

        model = lgb.train(
            params,
            train_data,
            valid_sets=[train_data, val_data],
            valid_names=["train", "val"],
            num_boost_round=1000,
            callbacks=[lgb.early_stopping(50)],
        )

        return model

    def _generate_time_dataset_with_rank(
        self, df: pd.DataFrame, reference: Optional[lgb.Dataset] = None
    ) -> lgb.Dataset:
        """着順予測を含むタイム予測用データセット"""
        # 必要なカラムの存在確認と補完
        # タイムの確認
        if "タイム" not in df.columns:
            raise ValueError("'タイム'列がDataFrameに存在しません")

        # course_typeの補完
        if "course_type" not in df.columns:
            if "芝ダ障害コード" in df.columns:
                course_type_map = {"1": "芝", "2": "ダ", "3": "障"}
                df["course_type"] = (
                    df["芝ダ障害コード"].astype(str).map(course_type_map).fillna("芝")
                )
            else:
                df["course_type"] = "芝"

        # ground_conditionの補完
        if "ground_condition" not in df.columns:
            if "馬場状態" in df.columns:
                df["ground_condition"] = df["馬場状態"]
            else:
                df["ground_condition"] = "良"

        # course_lengthの補完
        if "course_length" not in df.columns:
            if "距離" in df.columns:
                df["course_length"] = df["距離"]
            else:
                raise ValueError(
                    f"course_length（距離）カラムが見つかりません\n"
                    f"利用可能なカラム: {sorted(df.columns.tolist())[:30]}..."
                )

        # タイムを正規化
        normalized_time = self._normalize_time(
            df["タイム"], df["course_length"], df["course_type"], df["ground_condition"]
        )

        # ペーススコアを計算
        race_pace_score = self._calculate_race_pace_score(df)

        # 特徴量にペーススコアと着順予測を追加
        df_with_features = df.copy()
        df_with_features["race_pace_score"] = race_pace_score

        # タイム正規化用に追加したobject型カラムを削除（LightGBM用）
        if (
            "course_type" in df_with_features.columns
            and df_with_features["course_type"].dtype == "object"
        ):
            if "e_course_type" in df_with_features.columns:
                df_with_features = df_with_features.drop(columns=["course_type"])
        if (
            "ground_condition" in df_with_features.columns
            and df_with_features["ground_condition"].dtype == "object"
        ):
            if "e_ground_condition" in df_with_features.columns:
                df_with_features = df_with_features.drop(columns=["ground_condition"])

        if "running_style" in df_with_features.columns:
            style_factor = (
                df_with_features["running_style"]
                .map({"逃げ": 1.0, "先行": 0.7, "中団": 0.3, "後方": 0.0})
                .fillna(0.5)
            )
            df_with_features["pace_running_style_interaction"] = race_pace_score * style_factor
        else:
            df_with_features["pace_running_style_interaction"] = race_pace_score * 0.5

        # 特徴量を取得（エンコード済みカラムのみを使用）
        available_features = []
        for f in self.encoded_feature_names:
            if f in df_with_features.columns:
                # object型のカラムは除外（e_*カラムを使用）
                if df_with_features[f].dtype != "object":
                    available_features.append(f)
                # object型の場合は、対応するe_*カラムが存在するか確認
                elif f.startswith("e_"):
                    # 既にe_*カラムの場合は追加（ただしobject型でないことを確認）
                    if df_with_features[f].dtype != "object":
                        available_features.append(f)

        # 追加特徴量
        if "predicted_rank" in df_with_features.columns:
            available_features.append("predicted_rank")
        available_features.extend(["race_pace_score", "pace_running_style_interaction"])

        # 最終的なフィルタリング（object型を完全に除外）
        features_for_lgb = []
        for feat in available_features:
            if feat in df_with_features.columns:
                # object型のカラムは完全に除外
                dtype = df_with_features[feat].dtype
                if dtype != "object" and str(dtype) != "object":
                    features_for_lgb.append(feat)

        # 使用した特徴量名を保存（予測時に使用）
        dataset = lgb.Dataset(
            df_with_features[features_for_lgb], label=normalized_time, reference=reference
        )
        # 特徴量名を保存（予測時に同じ順序で使用するため）
        dataset.feature_names = features_for_lgb
        return dataset

    def _get_features_for_prediction(
        self, df: pd.DataFrame, feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        予測用の特徴量を取得（学習時と同じ特徴量セット）

        Args:
            df: 予測対象のDataFrame
            feature_names: 学習時に使用した特徴量名のリスト（指定された場合、この順序で返す）
        """
        # 必要なカラムの補完（タイム正規化用）
        if "course_type" not in df.columns:
            if "芝ダ障害コード" in df.columns:
                course_type_map = {"1": "芝", "2": "ダ", "3": "障"}
                df["course_type"] = (
                    df["芝ダ障害コード"].astype(str).map(course_type_map).fillna("芝")
                )
            else:
                df["course_type"] = "芝"

        if "ground_condition" not in df.columns:
            if "馬場状態" in df.columns:
                df["ground_condition"] = df["馬場状態"]
            else:
                df["ground_condition"] = "良"

        if "course_length" not in df.columns:
            if "距離" in df.columns:
                df["course_length"] = df["距離"]
            else:
                raise ValueError("course_length（距離）カラムが見つかりません")

        # ペーススコアを計算
        race_pace_score = self._calculate_race_pace_score(df)

        df_with_pace = df.copy()
        df_with_pace["race_pace_score"] = race_pace_score

        # object型カラムを削除（学習時と同じ処理）
        if "course_type" in df_with_pace.columns and df_with_pace["course_type"].dtype == "object":
            if "e_course_type" in df_with_pace.columns:
                df_with_pace = df_with_pace.drop(columns=["course_type"])
        if (
            "ground_condition" in df_with_pace.columns
            and df_with_pace["ground_condition"].dtype == "object"
        ):
            if "e_ground_condition" in df_with_pace.columns:
                df_with_pace = df_with_pace.drop(columns=["ground_condition"])

        if "running_style" in df_with_pace.columns:
            style_factor = (
                df_with_pace["running_style"]
                .map({"逃げ": 1.0, "先行": 0.7, "中団": 0.3, "後方": 0.0})
                .fillna(0.5)
            )
            df_with_pace["pace_running_style_interaction"] = race_pace_score * style_factor
        else:
            df_with_pace["pace_running_style_interaction"] = race_pace_score * 0.5

        # 学習時と同じ特徴量を取得（object型を除外）
        if feature_names is not None:
            # 学習時に使用した特徴量名のリストを使用
            features_for_lgb = [f for f in feature_names if f in df_with_pace.columns]
        else:
            # デフォルトの処理
            available_features = []
            for f in self.encoded_feature_names:
                if f in df_with_pace.columns:
                    if df_with_pace[f].dtype != "object":
                        available_features.append(f)
                    elif f.startswith("e_"):
                        if df_with_pace[f].dtype != "object":
                            available_features.append(f)

            available_features.extend(["race_pace_score", "pace_running_style_interaction"])

            # 最終的なフィルタリング（object型を完全に除外）
            features_for_lgb = []
            for feat in available_features:
                if feat in df_with_pace.columns:
                    dtype = df_with_pace[feat].dtype
                    if dtype != "object" and str(dtype) != "object":
                        features_for_lgb.append(feat)

        # 不足している特徴量をNaNで補完（学習時と予測時で特徴量が異なる場合）
        for feat in features_for_lgb:
            if feat not in df_with_pace.columns:
                df_with_pace[feat] = np.nan

        return df_with_pace[features_for_lgb]

    @staticmethod
    def predict(
        models: dict[str, lgb.Booster], race_df: pd.DataFrame, features: Features
    ) -> pd.DataFrame:
        """
        予測を実行

        Args:
            models: {
                'rank_model': 第2段階の着順予測モデル（タイム予測を含む）,
                'time_model': 第3段階のタイム予測モデル（着順予測を含む）,
                'time_model_stage1': 第1段階のタイム予測モデル,
                'rank_model_stage1': 第1段階の着順予測モデル
            }
            race_df: 予測対象のDataFrame
            features: Featuresインスタンス

        Returns:
            予測結果が追加されたDataFrame
        """
        rank_model_v2 = models["rank_model"]  # 第2段階: タイム予測を含む着順予測モデル
        time_model_v2 = models["time_model"]  # 第3段階: 着順予測を含むタイム予測モデル
        time_model_stage1 = models.get("time_model_stage1")  # 第1段階: タイム予測モデル
        models.get("rank_model_stage1")  # 第1段階: 着順予測モデル

        # 予測用の特徴量を準備
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

        # _generate_time_datasetと同じ前処理を適用
        # course_typeの補完（文字列として）
        if "course_type" not in race_df_processed.columns:
            if "芝ダ障害コード" in race_df_processed.columns:
                course_type_map = {"1": "芝", "2": "ダ", "3": "障"}
                race_df_processed["course_type"] = (
                    race_df_processed["芝ダ障害コード"]
                    .astype(str)
                    .map(course_type_map)
                    .fillna("芝")
                )
            else:
                race_df_processed["course_type"] = "芝"

        # ground_conditionの補完（文字列として）
        if "ground_condition" not in race_df_processed.columns:
            if "馬場状態" in race_df_processed.columns:
                race_df_processed["ground_condition"] = race_df_processed["馬場状態"]
            else:
                race_df_processed["ground_condition"] = "良"

        # course_lengthの補完
        if "course_length" not in race_df_processed.columns:
            if "距離" in race_df_processed.columns:
                race_df_processed["course_length"] = race_df_processed["距離"]
            else:
                raise ValueError("course_length（距離）カラムが見つかりません")

        # ペーススコアを計算
        predictor = ComplementaryPredictor(race_df_processed, race_df_processed)
        race_pace_score = predictor._calculate_race_pace_score(race_df_processed)
        race_df_processed["race_pace_score"] = race_pace_score

        if "running_style" in race_df_processed.columns:
            style_factor = (
                race_df_processed["running_style"]
                .map({"逃げ": 1.0, "先行": 0.7, "中団": 0.3, "後方": 0.0})
                .fillna(0.5)
            )
            race_df_processed["pace_running_style_interaction"] = race_pace_score * style_factor
        else:
            race_df_processed["pace_running_style_interaction"] = race_pace_score * 0.5

        # タイム正規化用に追加したobject型カラムを削除（LightGBM用）
        # course_type, ground_conditionは文字列なので、e_*カラムを使用
        # LightGBMは数値型のみ受け付けるため、object型は確実に削除
        object_columns_to_remove = []
        if (
            "course_type" in race_df_processed.columns
            and race_df_processed["course_type"].dtype == "object"
        ):
            object_columns_to_remove.append("course_type")
        if (
            "ground_condition" in race_df_processed.columns
            and race_df_processed["ground_condition"].dtype == "object"
        ):
            object_columns_to_remove.append("ground_condition")

        # その他のobject型カラムも削除（ただし、e_*カラムは数値型なので残す）
        for col in race_df_processed.columns:
            if (
                race_df_processed[col].dtype == "object"
                and col not in ["race_key"]
                and not col.startswith("e_")
            ):
                if col not in object_columns_to_remove:
                    object_columns_to_remove.append(col)

        if object_columns_to_remove:
            race_df_processed = race_df_processed.drop(columns=object_columns_to_remove)

        # 特徴量を取得（_generate_time_datasetと同じロジックを使用）
        # 1. encoded_feature_namesからobject型を除外
        available_features = []
        for f in features.encoded_feature_names:
            if f in race_df_processed.columns:
                # object型のカラムは除外（e_*カラムを使用）
                if race_df_processed[f].dtype != "object":
                    available_features.append(f)
                # object型の場合は、対応するe_*カラムが存在するか確認
                elif f.startswith("e_"):
                    # 既にe_*カラムの場合は追加（ただしobject型でないことを確認）
                    if race_df_processed[f].dtype != "object":
                        available_features.append(f)

        # 2. ペース関連の特徴量を追加
        available_features.extend(["race_pace_score", "pace_running_style_interaction"])

        # 3. 最終的なフィルタリング（object型を完全に除外）
        features_for_lgb = []
        for feat in available_features:
            if feat in race_df_processed.columns:
                dtype = race_df_processed[feat].dtype
                if dtype != "object" and str(dtype) != "object":
                    features_for_lgb.append(feat)

        # ステップ1: 第1段階のタイム予測モデルでタイムを予測（predicted_rankなし）
        if time_model_stage1 is None:
            raise ValueError(
                "time_model_stage1が提供されていません。学習時に第1段階のモデルも保存してください。"
            )

        # 学習時に使用された特徴量名を取得（モデルから取得）
        # LightGBMモデルはfeature_name()メソッドを持っている
        try:
            model_feature_names = time_model_stage1.feature_name()
            if model_feature_names and len(model_feature_names) > 0:
                # モデルが期待する特徴量名を順序通りに使用（モデルの順序を保持）
                # 重要: モデルの期待する順序で特徴量を提供する必要がある
                time_features_stage1 = []
                for f in model_feature_names:
                    if f in race_df_processed.columns:
                        # object型のカラムは除外（LightGBMは数値型のみ受け付ける）
                        if race_df_processed[f].dtype != "object":
                            time_features_stage1.append(f)

                # モデルが期待する特徴量がすべて存在するか確認
                if len(time_features_stage1) != len(model_feature_names):
                    missing_features = set(model_feature_names) - set(time_features_stage1)
                    # object型のカラムが除外された場合は警告のみ
                    object_missing = [
                        f
                        for f in missing_features
                        if f in race_df_processed.columns and race_df_processed[f].dtype == "object"
                    ]
                    if object_missing:
                        print(f"警告: object型の特徴量が除外されました: {object_missing}")
                        missing_features = missing_features - set(object_missing)

                    if missing_features:
                        raise ValueError(
                            f"タイム予測モデルが期待する特徴量が見つかりません: {missing_features}\n"
                            f"期待される特徴量数: {len(model_feature_names)}, 見つかった特徴量数: {len(time_features_stage1)}\n"
                            f"期待される特徴量: {model_feature_names[:10]}...\n"
                            f"利用可能な特徴量: {race_df_processed.columns.tolist()[:30]}..."
                        )
            else:
                # モデルから特徴量名を取得できない場合は、features_for_lgbを使用
                time_features_stage1 = features_for_lgb.copy()
        except (AttributeError, TypeError) as e:
            # モデルから特徴量名を取得できない場合は、features_for_lgbを使用
            print(f"警告: モデルから特徴量名を取得できませんでした: {e}")
            print(f"features_for_lgbを使用します（{len(features_for_lgb)}特徴量）")
            time_features_stage1 = features_for_lgb.copy()

        # 念のため、object型のカラムが含まれていないか確認
        object_features = [
            f for f in time_features_stage1 if race_df_processed[f].dtype == "object"
        ]
        if object_features:
            print(f"警告: object型の特徴量が検出されました。除外します: {object_features}")
            time_features_stage1 = [f for f in time_features_stage1 if f not in object_features]

        predicted_time_stage1 = time_model_stage1.predict(
            race_df_processed[time_features_stage1], num_iteration=time_model_stage1.best_iteration
        )
        race_df_processed["predicted_time"] = predicted_time_stage1

        # ステップ2: 第2段階の着順予測モデルで着順を予測（predicted_timeを含む）
        # object型のカラムを除外（LightGBMは数値型のみ受け付ける）
        rank_features = [
            f
            for f in features.encoded_feature_names
            if f in race_df_processed.columns and race_df_processed[f].dtype != "object"
        ]
        if "predicted_time" not in rank_features and "predicted_time" in race_df_processed.columns:
            rank_features.append("predicted_time")

        # 念のため、object型のカラムが含まれていないか確認
        object_features = [f for f in rank_features if race_df_processed[f].dtype == "object"]
        if object_features:
            print(f"警告: object型の特徴量が検出されました。除外します: {object_features}")
            rank_features = [f for f in rank_features if f not in object_features]

        predicted_rank = rank_model_v2.predict(
            race_df_processed[rank_features], num_iteration=rank_model_v2.best_iteration
        )
        race_df_processed["predicted_rank"] = predicted_rank

        # ステップ3: 第3段階のタイム予測モデルでタイムを再予測（predicted_rankを含む）
        # 第3段階のモデルは第1段階と同じ特徴量 + predicted_rankを使用
        try:
            model_feature_names_v2 = time_model_v2.feature_name()
            if model_feature_names_v2 and len(model_feature_names_v2) > 0:
                # モデルが期待する特徴量名を順序通りに使用（モデルの順序を保持）
                # 重要: モデルの期待する順序で特徴量を提供する必要がある
                time_features_v2 = []
                for f in model_feature_names_v2:
                    if f in race_df_processed.columns:
                        # object型のカラムは除外（LightGBMは数値型のみ受け付ける）
                        if race_df_processed[f].dtype != "object":
                            time_features_v2.append(f)

                # モデルが期待する特徴量がすべて存在するか確認
                if len(time_features_v2) != len(model_feature_names_v2):
                    missing_features = set(model_feature_names_v2) - set(time_features_v2)
                    # object型のカラムが除外された場合は警告のみ
                    object_missing = [
                        f
                        for f in missing_features
                        if f in race_df_processed.columns and race_df_processed[f].dtype == "object"
                    ]
                    if object_missing:
                        print(f"警告: object型の特徴量が除外されました: {object_missing}")
                        missing_features = missing_features - set(object_missing)

                    if missing_features:
                        raise ValueError(
                            f"タイム予測モデル（第3段階）が期待する特徴量が見つかりません: {missing_features}\n"
                            f"期待される特徴量数: {len(model_feature_names_v2)}, 見つかった特徴量数: {len(time_features_v2)}\n"
                            f"期待される特徴量: {model_feature_names_v2[:10]}...\n"
                            f"利用可能な特徴量: {race_df_processed.columns.tolist()[:30]}..."
                        )
            else:
                # モデルから特徴量名を取得できない場合は、features_for_lgb + predicted_rankを使用
                time_features_v2 = features_for_lgb.copy()
                if (
                    "predicted_rank" not in time_features_v2
                    and "predicted_rank" in race_df_processed.columns
                ):
                    time_features_v2.append("predicted_rank")
        except (AttributeError, TypeError) as e:
            # モデルから特徴量名を取得できない場合は、features_for_lgb + predicted_rankを使用
            print(f"警告: モデルから特徴量名を取得できませんでした: {e}")
            print("features_for_lgb + predicted_rankを使用します")
            time_features_v2 = features_for_lgb.copy()
            if (
                "predicted_rank" not in time_features_v2
                and "predicted_rank" in race_df_processed.columns
            ):
                time_features_v2.append("predicted_rank")

        # 念のため、object型のカラムが含まれていないか確認
        object_features = [f for f in time_features_v2 if race_df_processed[f].dtype == "object"]
        if object_features:
            print(f"警告: object型の特徴量が検出されました。除外します: {object_features}")
            time_features_v2 = [f for f in time_features_v2 if f not in object_features]

        predicted_time_normalized = time_model_v2.predict(
            race_df_processed[time_features_v2], num_iteration=time_model_v2.best_iteration
        )

        result_df = race_df_processed.copy()
        result_df.insert(0, "predict_rank", np.round(predicted_rank, 2))
        result_df.insert(1, "predict_time_normalized", np.round(predicted_time_normalized, 4))

        return result_df
