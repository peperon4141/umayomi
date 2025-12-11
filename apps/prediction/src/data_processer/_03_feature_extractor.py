"""特徴量抽出処理（前走データと統計特徴量）"""

import gc
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Union

import pandas as pd

from ._03_02_previous_race_extractor import PreviousRaceExtractor
from src.utils.feature_converter import FeatureConverter
from src.utils.schema_loader import Schema, Column
from ._03_03_horse_statistics import HorseStatistics
from ._03_04_jockey_statistics import JockeyStatistics
from ._03_05_trainer_statistics import TrainerStatistics


class FeatureExtractor:
    """特徴量を抽出するクラス（前走データと統計特徴量、staticメソッドのみ）"""
    
    # 結合キー
    MERGE_KEYS = ["race_key", "馬番"]
    
    # 統計量計算用カラム
    STATS_COLUMNS = {"race_key", "馬番", "血統登録番号", "騎手コード", "調教師コード", "着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"}
    
    # 統計量計算用のソース
    STATS_SOURCES = ["SED", "BAC", "KYI"]
    
    # 環境変数
    ENV_FEATURE_EXTRACTOR_MAX_WORKERS = "FEATURE_EXTRACTOR_MAX_WORKERS"
    DEFAULT_FEATURE_EXTRACTOR_WORKERS = 2

    @staticmethod
    def extract_all_parallel(
        combined_df: pd.DataFrame, historical_sed_df: pd.DataFrame, bac_df: pd.DataFrame, full_info_schema: Dict,
        horse_statistics_schema: Union[Dict, Schema], jockey_statistics_schema: Union[Dict, Schema],
        trainer_statistics_schema: Union[Dict, Schema], previous_race_extractor_schema: Union[Dict, Schema],
        feature_extraction_schema: Union[Dict, Schema]
    ) -> pd.DataFrame:
        """
        前走データと統計特徴量を並列処理で抽出。
        
        Args:
            combined_df: 結合済みDataFrame（特定年度のKYI/BAC/SED等を結合済み、start_datetime計算済み）
            historical_sed_df: 複数年度のSEDデータ（前走データ抽出と統計量計算用、過去年度を含む）
            bac_df: BACデータ（historical_sed_dfにrace_keyを追加するために必要）
            full_info_schema: スキーマ情報（必須）
        
        Returns:
            全特徴量が追加されたDataFrame
        """
        if historical_sed_df is None: return combined_df
        if bac_df is None: raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        if full_info_schema is None: raise ValueError("full_info_schemaは必須です。スキーマ情報が提供されていません。")

        target_df = combined_df.copy()
        # 年齢カラムを生成（_04_01_numeric_converterの_add_computed_fieldsを呼び出し）
        from ._04_01_numeric_converter import NumericConverter
        NumericConverter._add_computed_fields(target_df)
        historical_sed_df_with_key = FeatureConverter.add_race_key_to_df(historical_sed_df, bac_df=bac_df, use_bac_date=True)
        
        # 統計量計算用のDataFrameを準備
        stats_columns = FeatureExtractor._get_stats_columns_from_schema(full_info_schema)
        available_stats_columns = [col for col in stats_columns if col in historical_sed_df_with_key.columns]
        if len(available_stats_columns) == 0: raise ValueError("統計量計算に必要なカラムがhistorical_sed_df_with_keyに存在しません。")
        
        historical_stats_df = historical_sed_df_with_key[available_stats_columns].copy()
        historical_stats_df["rank_1st"] = (historical_stats_df["着順"] == 1).astype(int)
        historical_stats_df["rank_3rd"] = (historical_stats_df["着順"].isin([1, 2, 3])).astype(int)
        historical_stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(historical_stats_df["race_key"])

        # 並列処理実行
        max_workers = int(os.environ.get(FeatureExtractor.ENV_FEATURE_EXTRACTOR_MAX_WORKERS, FeatureExtractor.DEFAULT_FEATURE_EXTRACTOR_WORKERS))
        results = {}
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(PreviousRaceExtractor.extract, target_df, previous_race_extractor_schema): "previous_races",
                    executor.submit(HorseStatistics.calculate, historical_stats_df, target_df, horse_statistics_schema): "horse_stats",
                    executor.submit(JockeyStatistics.calculate, historical_stats_df, target_df, jockey_statistics_schema): "jockey_stats",
                    executor.submit(TrainerStatistics.calculate, historical_stats_df, target_df, trainer_statistics_schema): "trainer_stats",
                }

                for future in as_completed(futures):
                    task_name = futures[future]
                    try:
                        results[task_name] = future.result()
                    except Exception as e:
                        raise RuntimeError(f"{task_name}でエラー: {e}") from e

            # 結果を結合（race_keyと馬番をキーとしてマージ）
            featured_df = results["previous_races"]
            existing_cols = set(featured_df.columns)

            # 統計結果を順次結合
            for stats_result_df in [results["horse_stats"], results["jockey_stats"], results["trainer_stats"]]:
                new_cols = [col for col in stats_result_df.columns if col not in target_df.columns and col not in existing_cols and col not in FeatureExtractor.MERGE_KEYS]
                if not new_cols: continue
                stats_subset = stats_result_df[FeatureExtractor.MERGE_KEYS + new_cols]
                featured_df = featured_df.merge(stats_subset, on=FeatureExtractor.MERGE_KEYS, how="left")
                existing_cols.update(new_cols)
            
            # 重複カラムの検証
            duplicated_cols = featured_df.columns[featured_df.columns.duplicated()].unique()
            if len(duplicated_cols) > 0: raise ValueError(f"重複カラムが検出されました: {list(duplicated_cols)[:20]}")

            # スキーマ検証
            schema_obj = Schema.from_dict(feature_extraction_schema) if isinstance(feature_extraction_schema, dict) else feature_extraction_schema
            schema_obj.validate(featured_df)

            return featured_df
        finally:
            # クリーンアップ
            del target_df, historical_sed_df_with_key, historical_stats_df, results
            gc.collect()

    @staticmethod
    def _get_stats_columns_from_schema(full_info_schema: Union[Dict, Schema]) -> list[str]:
        """統計量計算に必要なカラムをスキーマから取得"""
        # Schemaオブジェクトの場合は辞書に変換
        if isinstance(full_info_schema, Schema):
            columns = full_info_schema.columns
        else:
            if "columns" not in full_info_schema: raise ValueError("full_info_schemaにcolumnsが定義されていません。スキーマファイルを確認してください。")
            columns = full_info_schema["columns"]
        
        available_columns = ["race_key"]
        for col_def in columns:
            # Columnオブジェクトまたは辞書のどちらでも対応
            if isinstance(col_def, Column):
                col_name, col_source = col_def.name, col_def.source
            else:
                if "name" not in col_def: raise ValueError("スキーマのカラム定義にnameが含まれていません。スキーマファイルを確認してください。")
                if "source" not in col_def: raise ValueError("スキーマのカラム定義にsourceが含まれていません。スキーマファイルを確認してください。")
                col_name, col_source = col_def["name"], col_def["source"]
            
            if col_name in FeatureExtractor.STATS_COLUMNS and col_source in FeatureExtractor.STATS_SOURCES and col_name not in available_columns:
                available_columns.append(col_name)
        
        return available_columns

