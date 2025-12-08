"""特徴量抽出処理（前走データと統計特徴量）"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict

import pandas as pd

from ._03_02_previous_race_extractor import PreviousRaceExtractor
from src.utils.feature_converter import FeatureConverter
from ._03_03_horse_statistics import HorseStatistics
from ._03_04_jockey_statistics import JockeyStatistics
from ._03_05_trainer_statistics import TrainerStatistics


class FeatureExtractor:
    """特徴量を抽出するクラス（前走データと統計特徴量、staticメソッドのみ）"""
    
    # 結合キー
    MERGE_KEYS = ["race_key", "馬番"]
    
    # 統計量計算用カラム
    STATS_COLUMNS = {
        "race_key",
        "馬番",
        "血統登録番号",
        "騎手コード",
        "調教師コード",
        "着順",
        "タイム",
        "距離",
        "芝ダ障害コード",
        "馬場状態",
        "頭数",
        "R",
    }
    
    # 環境変数
    ENV_FEATURE_EXTRACTOR_MAX_WORKERS = "FEATURE_EXTRACTOR_MAX_WORKERS"
    DEFAULT_FEATURE_EXTRACTOR_WORKERS = 2

    @staticmethod
    def extract_previous_races(
        df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: pd.DataFrame, full_info_schema: Dict, previous_race_extractor_schema: Dict
    ) -> pd.DataFrame:
        """前走データを抽出。df: 結合済みDataFrame、sed_df: SEDデータ、bac_df: BACデータ（必須）。前走データが追加されたDataFrameを返す"""
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        if full_info_schema is None:
            raise ValueError("full_info_schemaは必須です。スキーマ情報が提供されていません。")
        return PreviousRaceExtractor.extract(df, sed_df, bac_df, full_info_schema, previous_race_extractor_schema)

    @staticmethod
    def extract_all_parallel(
        df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: pd.DataFrame, full_info_schema: Dict,
        horse_statistics_schema: Dict, jockey_statistics_schema: Dict,
        trainer_statistics_schema: Dict, previous_race_extractor_schema: Dict
    ) -> pd.DataFrame:
        """
        前走データと統計特徴量を並列処理で抽出。
        
        Args:
            df: 結合済みDataFrame（SEDデータも含む）
            sed_df: SEDデータ（前走データ抽出用、複数年度）
            bac_df: BACデータ（必須）
            full_info_schema: スキーマ情報（必須）
        
        Returns:
            全特徴量が追加されたDataFrame
        """
        if sed_df is None:
            return df
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        if full_info_schema is None:
            raise ValueError("full_info_schemaは必須です。スキーマ情報が提供されていません。")

        # 前処理：共通データ準備
        # add_start_datetime_to_df内でcopy()が実行されるため、ここでのcopy()は不要
        df_with_datetime = FeatureConverter.add_start_datetime_to_df(df)
        sed_df_with_key = FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
        
        # スキーマから統計量計算に必要なカラムを取得
        stats_columns = FeatureExtractor._get_stats_columns_from_schema(full_info_schema)
        
        # 実際に存在するカラムのみを抽出
        available_stats_columns = [col for col in stats_columns if col in sed_df_with_key.columns]
        if len(available_stats_columns) == 0:
            raise ValueError("統計量計算に必要なカラムがsed_df_with_keyに存在しません。")
        
        # 必要な列のみを抽出（新しい列を追加するため、コピーが必要）
        stats_df = sed_df_with_key[available_stats_columns].copy()
        stats_df["rank_1st"] = (stats_df["着順"] == 1).astype(int)
        stats_df["rank_3rd"] = (stats_df["着順"].isin([1, 2, 3])).astype(int)
        stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(stats_df["race_key"])

        # 並列処理実行
        max_workers = int(os.environ.get(FeatureExtractor.ENV_FEATURE_EXTRACTOR_MAX_WORKERS, FeatureExtractor.DEFAULT_FEATURE_EXTRACTOR_WORKERS))
        results = {}
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(PreviousRaceExtractor.extract, df_with_datetime, sed_df, bac_df, full_info_schema, previous_race_extractor_schema): "previous_races",
                    executor.submit(HorseStatistics.calculate, stats_df, df_with_datetime, horse_statistics_schema): "horse_stats",
                    executor.submit(JockeyStatistics.calculate, stats_df, df_with_datetime, jockey_statistics_schema): "jockey_stats",
                    executor.submit(TrainerStatistics.calculate, stats_df, df_with_datetime, trainer_statistics_schema): "trainer_stats",
                }

                for future in as_completed(futures):
                    task_name = futures[future]
                    try:
                        results[task_name] = future.result()
                    except Exception as e:
                        raise RuntimeError(f"{task_name}でエラー: {e}") from e

            # 結果を結合（race_keyと馬番をキーとしてマージ）
            featured_df = results["previous_races"]

            # 既に含まれているカラムを追跡
            existing_cols = set(featured_df.columns)

            # 統計結果を結合
            for stats_name, stats_df in [("horse_stats", results["horse_stats"]), ("jockey_stats", results["jockey_stats"]), ("trainer_stats", results["trainer_stats"])]:
                new_cols = [
                    col for col in stats_df.columns 
                    if col not in df_with_datetime.columns and col not in existing_cols and col not in FeatureExtractor.MERGE_KEYS
                ]
                if new_cols:
                    stats_subset = stats_df[FeatureExtractor.MERGE_KEYS + new_cols]
                    featured_df = featured_df.merge(stats_subset, on=FeatureExtractor.MERGE_KEYS, how="left")
                    existing_cols.update(new_cols)
            
            # 重複カラムの検証
            duplicated_cols = featured_df.columns[featured_df.columns.duplicated()].unique()
            if len(duplicated_cols) > 0:
                raise ValueError(f"重複カラムが検出されました: {list(duplicated_cols)[:20]}")

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
            import gc
            gc.collect()

    @staticmethod
    def _get_stats_columns_from_schema(full_info_schema: Dict) -> list[str]:
        """
        統計量計算に必要なカラムをスキーマから取得
        スキーマのsourceフィールドを使用して、SED、BAC、KYIから必要なカラムを動的に取得
        
        Args:
            full_info_schema: full_info_schema.jsonの内容
            
        Returns:
            統計量計算に必要なカラム名のリスト
        """
        # スキーマからsourceがSED、BAC、KYIのカラムを取得
        available_columns = ["race_key"]  # race_keyは常に必要
        
        if "columns" not in full_info_schema: raise ValueError("full_info_schemaにcolumnsが定義されていません。スキーマファイルを確認してください。")
        for col_def in full_info_schema["columns"]:
            if "name" not in col_def: raise ValueError("スキーマのカラム定義にnameが含まれていません。スキーマファイルを確認してください。")
            if "source" not in col_def: raise ValueError("スキーマのカラム定義にsourceが含まれていません。スキーマファイルを確認してください。")
            col_name = col_def["name"]
            col_source = col_def["source"]
            
            # 必要なカラム名で、かつsourceがSED、BAC、KYIのいずれか
            if col_name in FeatureExtractor.STATS_COLUMNS and col_source in ["SED", "BAC", "KYI"]:
                if col_name not in available_columns:
                    available_columns.append(col_name)
        
        return available_columns

