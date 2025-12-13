"""日次データ予測実行モジュール"""

import gc
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import lightgbm as lgb
import pandas as pd

from src.data_processer._02_jrdb_combiner import JrdbCombiner
from src.data_processer._03_feature_extractor import FeatureExtractor
from src.data_processer._04_key_converter import KeyConverter
from src.feature_enhancers import enhance_features
from src.features import Features
from src.jrdb_scraper.convert_local_folder_to_parquet import convert_local_folder_to_parquet
from src.jrdb_scraper.entities.jrdb import JRDBDataType
from src.rank_predictor import RankPredictor
from src.utils.jrdb_format_loader import JRDBFormatLoader
from src.utils.parquet_loader import ParquetLoader
from src.utils.schema_loader import Schema, SchemaFile, SchemaLoader


class PredictionExecutor:
    """日次データの予測を実行するクラス"""

    @staticmethod
    def execute_daily_prediction(
        date_str: str,
        model_path: str,
        daily_data_path: str,
        base_path: Path,
        parquet_base_path: Path,
        output_path: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        日次データの予測を実行するメインメソッド
        
        Args:
            date_str: 日付文字列（例: "2025-11-30"）
            model_path: モデルファイルのパス
            daily_data_path: 日次データのパス（`data/daily`）
            base_path: プロジェクトルートパス
            parquet_base_path: Parquetファイルのベースパス
            output_path: 出力先パス（オプション）
        
        Returns:
            予測結果のDataFrame
        """
        # 日付から年度を取得
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        year = date_obj.year
        
        # 1. 日次LZHファイルをParquetに変換
        daily_parquet_path = parquet_base_path / "daily" / date_str
        PredictionExecutor._convert_daily_lzh_to_parquet(
            daily_data_path, date_str, year, daily_parquet_path
        )
        
        # 2. 日次データを前処理（特徴量抽出まで）
        featured_df = PredictionExecutor._process_daily_data_for_prediction(
            daily_parquet_path, year, base_path, parquet_base_path
        )
        
        # 3. 日次データを変換（キー変換、数値化、データ型最適化）
        converted_df, featured_df_sorted = PredictionExecutor._convert_daily_data(
            featured_df, base_path
        )
        
        # 4. 特徴量強化
        converted_df = enhance_features(converted_df, race_key_col="race_key")
        
        # 5. モデル読み込み
        model = PredictionExecutor._load_model(model_path)
        
        # 6. 予測実行（featured_df_sortedから馬番を取得するために渡す）
        predictions_df = PredictionExecutor._execute_prediction(
            model, converted_df, featured_df_sorted
        )
        
        # 7. 予測結果を整形
        results_df = PredictionExecutor._format_prediction_results(
            predictions_df, featured_df
        )
        
        # 8. JSON形式で保存
        if output_path:
            PredictionExecutor._save_results_to_json(
                results_df, date_str, output_path
            )
        
        return results_df

    @staticmethod
    def _convert_daily_lzh_to_parquet(
        daily_data_path: str,
        date_str: str,
        year: int,
        output_dir: Path,
    ) -> None:
        """
        日次LZHファイルを読み込んでParquetに変換
        
        Args:
            daily_data_path: 日次データのパス
            date_str: 日付文字列（例: "2025-11-30"）
            year: 年度
            output_dir: 出力ディレクトリ
        """
        # 日次データフォルダのパスを構築
        # まず data/daily/MM/DD を試し、存在しない場合は data/daily を直接使用
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        daily_folder = Path(daily_data_path) / f"{date_obj.month:02d}" / f"{date_obj.day:02d}"
        
        if not daily_folder.exists():
            # data/daily/MM/DD が存在しない場合は、data/daily を直接使用
            daily_folder = Path(daily_data_path)
            if not daily_folder.exists():
                raise FileNotFoundError(f"日次データフォルダが見つかりません: {daily_data_path}")
        
        # 必要なデータタイプ: BAC, KYI, UKC, TYB（SEDは不要）
        data_types = [
            JRDBDataType.BAC,
            JRDBDataType.KYI,
            JRDBDataType.UKC,
            JRDBDataType.TYB,
        ]
        
        # Parquet変換を実行
        output_dir.mkdir(parents=True, exist_ok=True)
        results = convert_local_folder_to_parquet(
            daily_folder, year, data_types, output_dir
        )
        
        # エラーチェック（UKCとTYBはオプショナルなので、必須データタイプのみチェック）
        required_data_types = [JRDBDataType.BAC.value, JRDBDataType.KYI.value]
        failed_results = [
            r for r in results 
            if not r.get("success", False) and r.get("dataType") in required_data_types
        ]
        if failed_results:
            error_messages = [f"{r['dataType']}: {r.get('error', 'Unknown error')}" for r in failed_results]
            raise ValueError(f"Parquet変換に失敗しました（必須データタイプ）: {', '.join(error_messages)}")
        
        # オプショナルデータタイプの警告
        optional_failed_results = [
            r for r in results 
            if not r.get("success", False) and r.get("dataType") not in required_data_types
        ]
        if optional_failed_results:
            warning_messages = [f"{r['dataType']}: {r.get('error', 'Unknown error')}" for r in optional_failed_results]
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"オプショナルデータタイプのParquet変換に失敗しました（処理は続行します）: {', '.join(warning_messages)}")

    @staticmethod
    def _process_daily_data_for_prediction(
        daily_parquet_path: Path,
        year: int,
        base_path: Path,
        parquet_base_path: Path,
    ) -> pd.DataFrame:
        """
        日次データを前処理（特徴量抽出まで）
        
        Args:
            daily_parquet_path: 日次Parquetファイルのパス
            year: 年度
            base_path: プロジェクトルートパス
            parquet_base_path: Parquetファイルのベースパス
        
        Returns:
            特徴量抽出済みDataFrame
        """
        # スキーマローダーを初期化
        schemas_base_path = base_path / "packages" / "data" / "schemas"
        schema_loader = SchemaLoader(schemas_base_path)
        formats_dir = base_path / "apps" / "prediction" / "src" / "jrdb_scraper" / "formats"
        format_loader = JRDBFormatLoader(formats_dir)
        
        # スキーマを読み込み（日次データ用のスキーマを使用）
        # 日次データ用のスキーマファイルを直接読み込む
        executor_schemas_dir = base_path / "packages" / "data" / "schemas" / "executor"
        daily_combined_schema_path = executor_schemas_dir / "_02_daily_combined_schema.json"
        if daily_combined_schema_path.exists():
            import json
            with open(daily_combined_schema_path, "r", encoding="utf-8") as f:
                combined_schema_dict = json.load(f)
            combined_schema = Schema.from_dict(combined_schema_dict)
        else:
            # フォールバック: 通常のスキーマを使用（警告を出す）
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"日次データ用のスキーマが見つかりません。通常のスキーマを使用します: {daily_combined_schema_path}")
            combined_schema = schema_loader.load_schema(SchemaFile.COMBINED)
        feature_extraction_schema = schema_loader.load_schema(SchemaFile.FEATURE_EXTRACTION)
        horse_statistics_schema = schema_loader.load_schema(SchemaFile.HORSE_STATISTICS)
        jockey_statistics_schema = schema_loader.load_schema(SchemaFile.JOCKEY_STATISTICS)
        trainer_statistics_schema = schema_loader.load_schema(SchemaFile.TRAINER_STATISTICS)
        previous_race_extractor_schema_02 = schema_loader.load_schema(SchemaFile.PREVIOUS_RACE_EXTRACTOR_02)
        
        # Parquetローダーを初期化
        parquet_loader = ParquetLoader(daily_parquet_path)
        
        # 日次データを読み込む（SEDは除外）
        kyi_df = parquet_loader.load_annual_pack_parquet("KYI", year, raise_on_not_found=True)
        bac_df = parquet_loader.load_annual_pack_parquet("BAC", year, raise_on_not_found=True)
        ukc_df = parquet_loader.load_annual_pack_parquet("UKC", year, raise_on_not_found=False)
        tyb_df = parquet_loader.load_annual_pack_parquet("TYB", year, raise_on_not_found=False)
        
        # データ結合（SEDは除外）
        data_dict = {
            JRDBDataType.KYI: kyi_df,
            JRDBDataType.BAC: bac_df,
        }
        if ukc_df is not None:
            data_dict[JRDBDataType.UKC] = ukc_df
        if tyb_df is not None:
            data_dict[JRDBDataType.TYB] = tyb_df
        
        raw_df = JrdbCombiner.combine(data_dict, combined_schema, format_loader)
        
        # 不要なDataFrameを削除
        del kyi_df, ukc_df, tyb_df
        gc.collect()
        
        # 前走データ抽出用のSED/BACデータを読み込み（過去年度のデータ）
        # DataProcessor._load_sed_bac_for_yearを流用
        parquet_loader_annual = ParquetLoader(parquet_base_path)
        previous_years = [y for y in range(year - 5, year) if y >= 2000]
        if not previous_years:
            previous_years = [year]
        
        sed_dfs = []
        bac_dfs = []
        for prev_year in previous_years:
            try:
                sed_df = parquet_loader_annual.load_annual_pack_parquet("SED", prev_year, raise_on_not_found=False)
                if sed_df is not None and len(sed_df) > 0:
                    sed_dfs.append(sed_df)
                bac_df_prev = parquet_loader_annual.load_annual_pack_parquet("BAC", prev_year, raise_on_not_found=False)
                if bac_df_prev is not None and len(bac_df_prev) > 0:
                    bac_dfs.append(bac_df_prev)
            except (FileNotFoundError, ValueError):
                continue
        
        sed_df = None
        if sed_dfs:
            sed_df = sed_dfs[0]
            for df in sed_dfs[1:]:
                sed_df = pd.concat([sed_df, df], ignore_index=True)
                del df
                gc.collect()
        
        bac_df_for_history = None
        if bac_dfs:
            bac_df_for_history = bac_dfs[0]
            for df in bac_dfs[1:]:
                bac_df_for_history = pd.concat([bac_df_for_history, df], ignore_index=True)
                del df
                gc.collect()
        
        if bac_df_for_history is None:
            raise ValueError(f"前走データ抽出用のBACデータが存在しません。年度: {year}")
        
        # 特徴量抽出
        try:
            featured_df = FeatureExtractor.extract_all_parallel(
                raw_df, sed_df, bac_df_for_history, feature_extraction_schema,
                horse_statistics_schema, jockey_statistics_schema,
                trainer_statistics_schema, previous_race_extractor_schema_02,
                feature_extraction_schema
            )
            del raw_df, sed_df, bac_df_for_history
            gc.collect()
            return featured_df
        finally:
            if 'raw_df' in locals():
                del raw_df
            if 'sed_df' in locals():
                del sed_df
            if 'bac_df_for_history' in locals():
                del bac_df_for_history
            gc.collect()

    @staticmethod
    def _convert_daily_data(
        featured_df: pd.DataFrame,
        base_path: Path,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        日次データを変換（キー変換、数値化、データ型最適化）
        
        Args:
            featured_df: 特徴量抽出済みDataFrame
            base_path: プロジェクトルートパス
        
        Returns:
            (変換済みDataFrame, ソート済みfeatured_df)のタプル
        """
        # スキーマローダーを初期化
        schemas_base_path = base_path / "packages" / "data" / "schemas"
        schema_loader = SchemaLoader(schemas_base_path)
        
        # スキーマを読み込み
        key_mapping_schema = schema_loader.load_schema(SchemaFile.KEY_MAPPING)
        training_schema = schema_loader.load_schema(SchemaFile.TRAINING)
        category_mappings = schema_loader.load_category_mappings()
        
        # データ変換前にfeatured_dfの順序を保持（race_keyと馬番でソート）
        featured_df_sorted = featured_df.copy()
        if featured_df_sorted.index.name == "race_key":
            featured_df_sorted = featured_df_sorted.reset_index()
        if "race_key" in featured_df_sorted.columns and "馬番" in featured_df_sorted.columns:
            featured_df_sorted = featured_df_sorted.sort_values(["race_key", "馬番"], ascending=True)
        
        # データ変換
        converted_df = KeyConverter.convert(
            featured_df_sorted, key_mapping_schema, training_schema, category_mappings
        )
        converted_df = KeyConverter.optimize(converted_df, training_schema)
        
        # race_keyをインデックスに設定（順序を保持）
        if "race_key" in converted_df.columns:
            converted_df.set_index("race_key", inplace=True)
            # start_datetimeでソートしない（元の順序を保持）
        
        return converted_df, featured_df_sorted

    @staticmethod
    def _load_model(model_path: str) -> lgb.Booster:
        """
        LightGBMモデルを読み込む
        
        Args:
            model_path: モデルファイルのパス
        
        Returns:
            LightGBMモデル
        """
        if not Path(model_path).exists():
            raise FileNotFoundError(f"モデルファイルが見つかりません: {model_path}")
        
        return lgb.Booster(model_file=model_path)

    @staticmethod
    def _execute_prediction(
        model: lgb.Booster,
        converted_df: pd.DataFrame,
        featured_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        予測を実行
        
        Args:
            model: LightGBMモデル
            converted_df: 変換済みDataFrame
            featured_df: 特徴量抽出済みDataFrame（馬番を含む）
        
        Returns:
            予測結果のDataFrame（race_key、馬番、predict列を含む）
        """
        # 予測実行
        features = Features()
        predictions_df = RankPredictor.predict(model, converted_df, features)
        
        # race_keyをカラムに戻す
        if predictions_df.index.name == "race_key":
            predictions_df = predictions_df.reset_index()
        
        # featured_dfからrace_keyと馬番の組み合わせを取得
        # converted_dfとfeatured_dfのインデックス（race_key）の順序が一致していることを前提とする
        featured_df_with_key = featured_df.copy()
        if featured_df_with_key.index.name == "race_key":
            featured_df_with_key = featured_df_with_key.reset_index()
        elif "race_key" not in featured_df_with_key.columns:
            raise ValueError("featured_dfにrace_keyが存在しません")
        
        if "馬番" not in featured_df_with_key.columns:
            raise ValueError("featured_dfに馬番が存在しません")
        
        # converted_dfのインデックス（race_key）の順序を保持
        converted_df_with_key = converted_df.copy()
        if converted_df_with_key.index.name == "race_key":
            converted_df_with_key = converted_df_with_key.reset_index()
        
        # converted_dfとfeatured_dfのrace_keyの順序が一致していることを確認
        # predictions_dfの行順序はconverted_dfの行順序と一致するため、
        # featured_dfから同じ順序で馬番を取得する
        if len(converted_df_with_key) != len(featured_df_with_key):
            raise ValueError(f"converted_dfとfeatured_dfの行数が一致しません: {len(converted_df_with_key)} vs {len(featured_df_with_key)}")
        
        # converted_dfの各行に対応する馬番を取得（行順序を保持）
        # predictions_dfの行順序はconverted_dfの行順序と一致するため、
        # converted_dfとfeatured_dfの行順序が一致していることを前提に、
        # featured_dfから直接馬番を取得する
        predictions_df["馬番"] = featured_df_with_key["馬番"].values
        
        return predictions_df

    @staticmethod
    def _format_prediction_results(
        predictions_df: pd.DataFrame,
        featured_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        予測結果を整形（race_key, 馬番, 予測スコア, 予測順位、その他基本情報を含む）
        
        Args:
            predictions_df: 予測結果のDataFrame（race_key、馬番、predict列を含む）
            featured_df: 特徴量抽出済みDataFrame（基本情報を含む）
        
        Returns:
            整形済み予測結果のDataFrame
        """
        # race_keyをカラムに戻す
        if predictions_df.index.name == "race_key":
            predictions_df = predictions_df.reset_index()
        
        # 基本情報をマージ
        featured_df_with_key = featured_df.copy()
        if featured_df_with_key.index.name == "race_key":
            featured_df_with_key = featured_df_with_key.reset_index()
        elif "race_key" not in featured_df_with_key.columns:
            raise ValueError("featured_dfにrace_keyが存在しません")
        
        # 必要なカラムのみを選択
        info_columns = ["race_key", "馬番", "馬名", "騎手名", "調教師名"]
        available_info_columns = [col for col in info_columns if col in featured_df_with_key.columns]
        featured_subset = featured_df_with_key[available_info_columns]
        
        # マージ（race_keyと馬番の両方でマージして重複を防ぐ）
        merge_keys = ["race_key", "馬番"]
        if "馬番" not in predictions_df.columns:
            raise ValueError("predictions_dfに馬番が存在しません")
        
        results_df = predictions_df.merge(
            featured_subset, on=merge_keys, how="left"
        )
        
        # 予測順位を計算（レースごとに予測スコアでソート）
        results_df["predicted_rank"] = results_df.groupby("race_key")["predict"].rank(
            ascending=False, method="min"
        ).astype(int)
        
        # カラム名を統一
        if "馬番" in results_df.columns:
            results_df = results_df.rename(columns={"馬番": "horse_number"})
        if "馬名" in results_df.columns:
            results_df = results_df.rename(columns={"馬名": "horse_name"})
        if "騎手名" in results_df.columns:
            results_df = results_df.rename(columns={"騎手名": "jockey_name"})
        if "調教師名" in results_df.columns:
            results_df = results_df.rename(columns={"調教師名": "trainer_name"})
        if "predict" in results_df.columns:
            results_df = results_df.rename(columns={"predict": "predicted_score"})
        
        return results_df

    @staticmethod
    def _save_results_to_json(
        results_df: pd.DataFrame,
        date_str: str,
        output_path: str,
    ) -> None:
        """
        予測結果をJSON Lines形式で保存（各馬1行、JSON Lines形式）
        
        Args:
            results_df: 予測結果のDataFrame
            date_str: 日付文字列
            output_path: 出力先パス
        """
        # 予測順位でソート
        results_df_sorted = results_df.sort_values(["race_key", "predicted_rank"])
        
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # JSON Lines形式で保存（各予測結果を1行で出力）
        with open(output_path_obj, "w", encoding="utf-8") as f:
            for _, row in results_df_sorted.iterrows():
                # horse_numberがNaNの場合はスキップ
                horse_number = row.get("horse_number")
                if pd.isna(horse_number):
                    continue
                
                prediction = {
                    "date": date_str,
                    "race_key": str(row.get("race_key", "")),
                    "horse_number": int(horse_number),
                    "horse_name": str(row.get("horse_name", "")),
                    "jockey_name": str(row.get("jockey_name", "")),
                    "trainer_name": str(row.get("trainer_name", "")),
                    "predicted_score": float(row.get("predict", row.get("predicted_score", 0.0))),
                    "predicted_rank": int(row.get("predicted_rank", 0)),
                }
                # 各予測結果を1行のJSONとして出力
                f.write(json.dumps(prediction, ensure_ascii=False) + "\n")

