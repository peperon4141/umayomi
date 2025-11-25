"""特徴量抽出処理（前走データと統計特徴量）"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional

import pandas as pd

from . import previous_race_extractor, statistical_feature_calculator
from .feature_converter import FeatureConverter
from .horse_statistics import HorseStatistics
from .jockey_statistics import JockeyStatistics
from .trainer_statistics import TrainerStatistics


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

    def extract_all_parallel(
        self, df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """前走データと統計特徴量を並列処理で抽出。df: 結合済みDataFrame、sed_df: SEDデータ、bac_df: BACデータ（オプション）。全特徴量が追加されたDataFrameを返す"""
        if sed_df is None:
            return df

        # 前処理：共通データ準備
        df_with_datetime = FeatureConverter.add_start_datetime_to_df(df.copy())
        if bac_df is not None:
            sed_df_with_key = FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
        else:
            sed_df_with_key = FeatureConverter.add_race_key_to_df(sed_df, use_bac_date=False)
        stats_df = sed_df_with_key[
            ["race_key", "馬番", "血統登録番号", "騎手コード", "調教師コード", "着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
        ].copy()
        stats_df["rank_1st"] = (stats_df["着順"] == 1).astype(int)
        stats_df["rank_3rd"] = (stats_df["着順"].isin([1, 2, 3])).astype(int)
        stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(stats_df["race_key"])

        # 並列処理実行
        print("特徴量抽出を並列処理中...")
        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(previous_race_extractor.extract, df_with_datetime.copy(), sed_df, bac_df): "previous_races",
                executor.submit(HorseStatistics.calculate, stats_df.copy(), df_with_datetime.copy()): "horse_stats",
                executor.submit(JockeyStatistics.calculate, stats_df.copy(), df_with_datetime.copy()): "jockey_stats",
                executor.submit(TrainerStatistics.calculate, stats_df.copy(), df_with_datetime.copy()): "trainer_stats",
            }

            for future in as_completed(futures):
                task_name = futures[future]
                try:
                    result_df = future.result()
                    results[task_name] = result_df
                    print(f"{task_name}完了")
                except Exception as e:
                    print(f"{task_name}でエラー: {e}")
                    raise

        # 結果を結合（元のインデックスで結合）
        print("結果を結合中...")
        featured_df = results["previous_races"]
        original_index = featured_df.index

        # 結合するDataFrameのリスト
        dfs_to_concat = [featured_df]

        # 馬統計を結合（追加されたカラムのみ）
        horse_new_cols = [col for col in results["horse_stats"].columns if col not in df_with_datetime.columns]
        if horse_new_cols:
            horse_stats_subset = results["horse_stats"][horse_new_cols].copy()
            horse_stats_subset.index = original_index
            dfs_to_concat.append(horse_stats_subset)

        # 騎手統計を結合（追加されたカラムのみ）
        jockey_new_cols = [col for col in results["jockey_stats"].columns if col not in df_with_datetime.columns]
        if jockey_new_cols:
            jockey_stats_subset = results["jockey_stats"][jockey_new_cols].copy()
            jockey_stats_subset.index = original_index
            dfs_to_concat.append(jockey_stats_subset)

        # 調教師統計を結合（追加されたカラムのみ）
        trainer_new_cols = [col for col in results["trainer_stats"].columns if col not in df_with_datetime.columns]
        if trainer_new_cols:
            trainer_stats_subset = results["trainer_stats"][trainer_new_cols].copy()
            trainer_stats_subset.index = original_index
            dfs_to_concat.append(trainer_stats_subset)

        # 一度に結合（フラグメント化を回避）
        if len(dfs_to_concat) > 1:
            featured_df = pd.concat(dfs_to_concat, axis=1)

        print("特徴量抽出完了")
        return featured_df

