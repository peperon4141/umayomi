"""特徴量抽出処理（前走データと統計特徴量）"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional

import pandas as pd

from ._03_02_previous_race_extractor import PreviousRaceExtractor
from ._03_01_feature_converter import FeatureConverter
from ._03_03_horse_statistics import HorseStatistics
from ._03_04_jockey_statistics import JockeyStatistics
from ._03_05_trainer_statistics import TrainerStatistics


class FeatureExtractor:
    """特徴量を抽出するクラス（前走データと統計特徴量、staticメソッドのみ）"""

    @staticmethod
    def extract_previous_races(
        df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: pd.DataFrame
    ) -> pd.DataFrame:
        """前走データを抽出。df: 結合済みDataFrame、sed_df: SEDデータ、bac_df: BACデータ（必須）。前走データが追加されたDataFrameを返す"""
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        return PreviousRaceExtractor.extract(df, sed_df, bac_df)

    @staticmethod
    def extract_all_parallel(
        df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: pd.DataFrame
    ) -> pd.DataFrame:
        """前走データと統計特徴量を並列処理で抽出。df: 結合済みDataFrame、sed_df: SEDデータ、bac_df: BACデータ（必須）。全特徴量が追加されたDataFrameを返す"""
        if sed_df is None:
            return df
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")

        # 前処理：共通データ準備
        # add_start_datetime_to_df内でcopy()が実行されるため、ここでのcopy()は不要
        df_with_datetime = FeatureConverter.add_start_datetime_to_df(df)
        sed_df_with_key = FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
        # 必要な列のみを抽出（列の抽出と新しい列の追加のため、コピーが必要だが、最小限に）
        # 列の抽出は新しいDataFrameを作成するため、明示的なcopy()は不要
        stats_df = sed_df_with_key[
            ["race_key", "馬番", "血統登録番号", "騎手コード", "調教師コード", "着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
        ]
        stats_df["rank_1st"] = (stats_df["着順"] == 1).astype(int)
        stats_df["rank_3rd"] = (stats_df["着順"].isin([1, 2, 3])).astype(int)
        stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(stats_df["race_key"])

        # 並列処理実行
        print("[_03_] 特徴量抽出を並列処理中...")
        # メモリ使用量を削減するため、環境変数でワーカー数を制御可能に
        max_workers = int(os.environ.get("FEATURE_EXTRACTOR_MAX_WORKERS", "2"))
        results = {}
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # メモリコピー削減: 統計計算関数は入力DataFrameを変更しないため、参照で渡す
                # previous_race_extractor.extractは関数内でcopy()するため、参照で渡す
                futures = {
                    executor.submit(PreviousRaceExtractor.extract, df_with_datetime, sed_df, bac_df): "previous_races",
                    executor.submit(HorseStatistics.calculate, stats_df, df_with_datetime): "horse_stats",
                    executor.submit(JockeyStatistics.calculate, stats_df, df_with_datetime): "jockey_stats",
                    executor.submit(TrainerStatistics.calculate, stats_df, df_with_datetime): "trainer_stats",
                }

                for future in as_completed(futures):
                    task_name = futures[future]
                    try:
                        result_df = future.result()
                        results[task_name] = result_df
                        print(f"[_03_] {task_name}完了")
                    except Exception as e:
                        print(f"[_03_] {task_name}でエラー: {e}")
                        raise

            # 結果を結合（元のインデックスで結合）
            print("[_03_] 結果を結合中...")
            featured_df = results["previous_races"]
            original_index = featured_df.index

            # デバッグ: 各結果のカラム数を確認
            print(f"[_03_] previous_racesカラム数: {len(featured_df.columns)}")
            print(f"[_03_] horse_statsカラム数: {len(results['horse_stats'].columns)}")
            print(f"[_03_] jockey_statsカラム数: {len(results['jockey_stats'].columns)}")
            print(f"[_03_] trainer_statsカラム数: {len(results['trainer_stats'].columns)}")
            print(f"[_03_] df_with_datetimeカラム数: {len(df_with_datetime.columns)}")

            # 結合するDataFrameのリスト
            dfs_to_concat = [featured_df]

            # 既に含まれているカラムを追跡（previous_racesに含まれる全カラム）
            existing_cols = set(featured_df.columns)

            # 馬統計を結合（追加されたカラムのみ、previous_racesに既に含まれているカラムは除外）
            horse_new_cols = [
                col for col in results["horse_stats"].columns 
                if col not in df_with_datetime.columns and col not in existing_cols
            ]
            # デバッグ: 重複チェック
            horse_duplicated = [col for col in results["horse_stats"].columns if col in existing_cols and col not in df_with_datetime.columns]
            if horse_duplicated:
                print(f"[_03_] 警告: 馬統計で重複カラム検出（previous_racesに既に存在）: {horse_duplicated[:10]}")
            if horse_new_cols:
                # 列の抽出は新しいDataFrameを作成するため、明示的なcopy()は不要
                horse_stats_subset = results["horse_stats"][horse_new_cols]
                horse_stats_subset.index = original_index
                dfs_to_concat.append(horse_stats_subset)
                existing_cols.update(horse_new_cols)

            # 騎手統計を結合（追加されたカラムのみ、previous_racesに既に含まれているカラムは除外）
            jockey_new_cols = [
                col for col in results["jockey_stats"].columns 
                if col not in df_with_datetime.columns and col not in existing_cols
            ]
            # デバッグ: 重複チェック
            jockey_duplicated = [col for col in results["jockey_stats"].columns if col in existing_cols and col not in df_with_datetime.columns]
            if jockey_duplicated:
                print(f"[_03_] 警告: 騎手統計で重複カラム検出（previous_racesに既に存在）: {jockey_duplicated[:10]}")
            if jockey_new_cols:
                # 列の抽出は新しいDataFrameを作成するため、明示的なcopy()は不要
                jockey_stats_subset = results["jockey_stats"][jockey_new_cols]
                jockey_stats_subset.index = original_index
                dfs_to_concat.append(jockey_stats_subset)
                existing_cols.update(jockey_new_cols)

            # 調教師統計を結合（追加されたカラムのみ、previous_racesに既に含まれているカラムは除外）
            trainer_new_cols = [
                col for col in results["trainer_stats"].columns 
                if col not in df_with_datetime.columns and col not in existing_cols
            ]
            # デバッグ: 重複チェック
            trainer_duplicated = [col for col in results["trainer_stats"].columns if col in existing_cols and col not in df_with_datetime.columns]
            if trainer_duplicated:
                print(f"[_03_] 警告: 調教師統計で重複カラム検出（previous_racesに既に存在）: {trainer_duplicated[:10]}")
            if trainer_new_cols:
                # 列の抽出は新しいDataFrameを作成するため、明示的なcopy()は不要
                trainer_stats_subset = results["trainer_stats"][trainer_new_cols]
                trainer_stats_subset.index = original_index
                dfs_to_concat.append(trainer_stats_subset)
                existing_cols.update(trainer_new_cols)

            # 一度に結合（フラグメント化を回避）
            if len(dfs_to_concat) > 1:
                featured_df = pd.concat(dfs_to_concat, axis=1)
                
                # 重複カラムの検証（データ整合性チェック）
                duplicated_cols = featured_df.columns[featured_df.columns.duplicated()].unique()
                if len(duplicated_cols) > 0:
                    raise ValueError(
                        f"重複カラムが検出されました。データ整合性を保つため、重複を解消してください。"
                        f"重複カラム: {list(duplicated_cols)[:20]}..." if len(duplicated_cols) > 20 else f"重複カラム: {list(duplicated_cols)}"
                    )

            print("[_03_] 特徴量抽出完了")
            return featured_df
        finally:
            # クリーンアップ: 不要なデータを削除
            if 'df_with_datetime' in locals():
                del df_with_datetime
            if 'sed_df_with_key' in locals():
                del sed_df_with_key
            if 'stats_df' in locals():
                del stats_df
            if 'results' in locals():
                del results
            if 'dfs_to_concat' in locals():
                del dfs_to_concat
            import gc
            gc.collect()

