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
        # historical SEDは一部レコードに場コード/回/Rなどの欠損が含まれることがある。
        # ここで無理な補完（fallback）は行わず、統計量計算に使えないレコードは明示的に除外する。
        required_cols = ["場コード", "回", "日", "R"]
        missing_required_cols = [c for c in required_cols if c not in historical_sed_df.columns]
        if missing_required_cols:
            raise ValueError(f"historical_sed_dfにrace_key生成必須カラムが存在しません: {missing_required_cols}")

        missing_rows = historical_sed_df[required_cols].isna().any(axis=1)
        if missing_rows.any():
            import logging
            logger = logging.getLogger(__name__)
            missing_count = int(missing_rows.sum())
            logger.warning(f"historical_sed_dfの必須カラム欠損行を除外します: {missing_count}/{len(historical_sed_df)}")
            historical_sed_df = historical_sed_df.loc[~missing_rows].copy()

        # historical SEDは自身が年月日を保持しているため、BACマッピングに依存せずにrace_keyを生成する
        if "年月日" not in historical_sed_df.columns:
            raise ValueError("historical_sed_dfに年月日カラムが存在しません。race_key生成に必須です。")

        # 年月日欠損も補完せず除外（fallback禁止）
        import logging
        logger = logging.getLogger(__name__)
        ymd_str = historical_sed_df["年月日"].apply(FeatureConverter.safe_ymd)
        invalid_ymd = ymd_str.str.len() != 8
        if invalid_ymd.any():
            invalid_count = int(invalid_ymd.sum())
            logger.warning(f"historical_sed_dfの年月日不正/欠損行を除外します: {invalid_count}/{len(historical_sed_df)}")
            historical_sed_df = historical_sed_df.loc[~invalid_ymd].copy()

        historical_sed_df_with_key = FeatureConverter.add_race_key_to_df(historical_sed_df, bac_df=None, use_bac_date=False)
        
        # 統計量計算用のDataFrameを準備
        stats_columns = FeatureExtractor._get_stats_columns_from_schema(full_info_schema)
        available_stats_columns = [col for col in stats_columns if col in historical_sed_df_with_key.columns]
        # start_datetime算出に必要なカラムはスキーマに含まれないことがあるため、必須として追加する
        for required_col in ["年月日", "発走時間"]:
            if required_col in historical_sed_df_with_key.columns and required_col not in available_stats_columns:
                available_stats_columns.append(required_col)
        if len(available_stats_columns) == 0: raise ValueError("統計量計算に必要なカラムがhistorical_sed_df_with_keyに存在しません。")
        
        historical_stats_df = historical_sed_df_with_key[available_stats_columns].copy()
        historical_stats_df["rank_1st"] = (historical_stats_df["着順"] == 1).astype(int)
        historical_stats_df["rank_3rd"] = (historical_stats_df["着順"].isin([1, 2, 3])).astype(int)
        historical_stats_df = FeatureConverter.add_start_datetime_to_df(historical_stats_df)

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

            # スキーマ検証（日次データなど、一部のカラムが存在しない場合は警告のみ）
            schema_obj = Schema.from_dict(feature_extraction_schema) if isinstance(feature_extraction_schema, dict) else feature_extraction_schema
            try:
                schema_obj.validate(featured_df)
            except ValueError as e:
                # 日次データなど、一部のカラムが存在しない場合は警告のみ（エラーにはしない）
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"スキーマ検証で警告: {e}（処理は続行します）")

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

