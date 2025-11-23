"""学習用データ準備モジュール（時系列分割、不要カラム除外、データ検証）"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd

from .features import Features

logger = logging.getLogger(__name__)


class TrainingDataPreparer:
    """学習用データ準備クラス。時系列分割、不要カラム除外、データ検証を行う。"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """初期化。base_path: プロジェクトのベースパス（デフォルト: 現在のディレクトリ）"""
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        self.schemas_dir = self.base_path / "packages" / "data" / "schemas" / "jrdb_processed"
        self.features = Features()

    def load_training_schema(self) -> Dict:
        """学習用データスキーマを読み込む"""
        schema_file = self.schemas_dir / "training_schema.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def prepare_training_data(
        self,
        df: pd.DataFrame,
        split_date: Union[str, datetime],
        features: Optional[Features] = None,
        validate: bool = True,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        学習用データを準備。元データをcopyで保持し、学習用データと評価用データを分離。

        Args:
            df: 結合済みDataFrame（元データ）
            split_date: 分割日時（"2024-06-01"形式の文字列またはdatetimeオブジェクト）
            features: Featuresインスタンス（省略時はデフォルトを使用）
            validate: データ検証を実行するかどうか

        Returns:
            (train_df, test_df, original_df)のタプル
            - train_df: 学習用データ（split_date以前、不要カラム除外）
            - test_df: テスト用データ（split_date以降、不要カラム除外）
            - original_df: 元データ（評価用カラムを含む完全なデータ）
        """
        if features is None:
            features = self.features

        # 元データをcopyで保持
        original_df = df.copy()

        # split_dateをdatetimeに変換
        if isinstance(split_date, str):
            split_date = pd.to_datetime(split_date)
        elif isinstance(split_date, datetime):
            split_date = pd.Timestamp(split_date)

        # start_datetimeが存在するか確認
        if "start_datetime" not in df.columns:
            raise ValueError("start_datetimeカラムが存在しません。データにstart_datetimeを追加してください。")

        # 時系列で分割
        train_df, test_df = self.split_train_test(df, split_date)

        # 学習に不要なカラムを除外（評価用カラムも含めて除外）
        excluded_cols = features.excluded_fields
        # 評価用カラム（オッズ、着順など）を取得（元データに保持するため）
        evaluation_cols = self.get_evaluation_columns(df, features)

        # 学習用データから除外カラムを削除（評価用カラムも除外）
        train_cols_to_remove = [col for col in train_df.columns if col in excluded_cols]
        test_cols_to_remove = [col for col in test_df.columns if col in excluded_cols]

        train_df = train_df.drop(columns=train_cols_to_remove, errors="ignore")
        test_df = test_df.drop(columns=test_cols_to_remove, errors="ignore")

        # データ検証
        if validate:
            schema = self.load_training_schema()
            self.validate_training_data(train_df, schema, "学習用データ")
            self.validate_training_data(test_df, schema, "テスト用データ")

        logger.info(f"学習用データ準備完了: 学習={len(train_df):,}行, テスト={len(test_df):,}行, 元データ={len(original_df):,}行")
        return train_df, test_df, original_df

    def split_train_test(
        self, df: pd.DataFrame, split_date: Union[str, datetime]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        時系列で学習/テストデータに分割。

        Args:
            df: 結合済みDataFrame
            split_date: 分割日時（"2024-06-01"形式の文字列またはdatetimeオブジェクト）

        Returns:
            (train_df, test_df)のタプル
        """
        if isinstance(split_date, str):
            split_date = pd.to_datetime(split_date)
        elif isinstance(split_date, datetime):
            split_date = pd.Timestamp(split_date)

        if "start_datetime" not in df.columns:
            raise ValueError("start_datetimeカラムが存在しません。")

        # start_datetimeが整数型（YYYYMMDDHHMM形式）の場合はdatetime型に変換
        if df["start_datetime"].dtype in ["int64", "int32", "int", "float64", "float32"]:
            # 整数型のstart_datetimeをdatetime型に変換
            start_datetime_dt = pd.to_datetime(df["start_datetime"].astype(str), format="%Y%m%d%H%M", errors="coerce")
            # 変換に失敗した場合は年月日のみで変換を試行
            mask = start_datetime_dt.isna()
            if mask.any():
                start_datetime_dt[mask] = pd.to_datetime(
                    df.loc[mask, "start_datetime"].astype(str).str[:8], format="%Y%m%d", errors="coerce"
                )
            train_mask = start_datetime_dt <= split_date
        else:
            # 既にdatetime型の場合
            train_mask = df["start_datetime"] <= split_date

        train_df = df[train_mask].copy()
        test_df = df[~train_mask].copy()

        logger.info(f"時系列分割: 分割日時={split_date}, 学習={len(train_df):,}行, テスト={len(test_df):,}行")
        return train_df, test_df

    def get_evaluation_columns(self, df: pd.DataFrame, features: Optional[Features] = None) -> List[str]:
        """
        評価用カラムを取得（オッズ、着順など）。

        Args:
            df: 結合済みDataFrame
            features: Featuresインスタンス（省略時はデフォルトを使用）

        Returns:
            評価用カラム名のリスト
        """
        if features is None:
            features = self.features

        # 評価用カラム（オッズ、着順など）を定義
        evaluation_keywords = ["オッズ", "着順", "rank", "単勝", "複勝", "確定"]
        evaluation_cols = []

        for col in df.columns:
            # 除外フィールドで、かつ評価用キーワードを含むカラム
            if col in features.excluded_fields:
                if any(keyword in col for keyword in evaluation_keywords):
                    evaluation_cols.append(col)
            # 着順（rank）も評価用
            elif col == "rank" or col == "着順":
                evaluation_cols.append(col)

        return evaluation_cols

    def validate_training_data(
        self, df: pd.DataFrame, schema: Optional[Dict] = None, data_name: str = "データ"
    ) -> None:
        """
        学習用データを検証。

        Args:
            df: 検証対象のDataFrame
            schema: スキーマ定義（省略時は自動読み込み）
            data_name: データ名（ログ出力用）

        Raises:
            ValueError: 検証に失敗した場合
        """
        if schema is None:
            schema = self.load_training_schema()

        errors = []
        warnings = []

        # 1. フィールド数検証
        expected_num_cols = schema.get("num_columns", 0)
        actual_num_cols = len(df.columns)
        if actual_num_cols != expected_num_cols:
            warnings.append(f"フィールド数が想定と異なります: 期待={expected_num_cols}, 実際={actual_num_cols}")

        # 2. 必須カラムの存在確認
        schema_columns = {col["name"] for col in schema.get("columns", [])}
        missing_cols = schema_columns - set(df.columns)
        if missing_cols:
            errors.append(f"必須カラムが存在しません: {sorted(missing_cols)}")

        # 3. データ欠落チェック（必須カラムの欠損値）
        for col_def in schema.get("columns", []):
            col_name = col_def["name"]
            if col_name in df.columns:
                missing_count = df[col_name].isna().sum()
                missing_rate = missing_count / len(df) * 100 if len(df) > 0 else 0
                if missing_rate > 50:  # 50%以上欠損している場合は警告
                    warnings.append(f"カラム '{col_name}' の欠損率が高いです: {missing_rate:.1f}% ({missing_count:,}件)")

        # 4. 時系列整合性チェック
        if "start_datetime" in df.columns:
            if df["start_datetime"].isna().any():
                warnings.append("start_datetimeに欠損値があります")
            # start_datetimeが整数型の場合はdatetime型に変換してチェック
            if df["start_datetime"].dtype in ["int64", "int32", "int", "float64", "float32"]:
                try:
                    start_datetime_dt = pd.to_datetime(df["start_datetime"].astype(str), format="%Y%m%d%H%M", errors="coerce")
                    mask = start_datetime_dt.isna()
                    if mask.any():
                        start_datetime_dt[mask] = pd.to_datetime(
                            df.loc[mask, "start_datetime"].astype(str).str[:8], format="%Y%m%d", errors="coerce"
                        )
                    min_date = start_datetime_dt.min()
                    max_date = start_datetime_dt.max()
                except Exception:
                    warnings.append("start_datetimeの日時変換に失敗しました")
                    min_date = None
                    max_date = None
            else:
                min_date = df["start_datetime"].min()
                max_date = df["start_datetime"].max()
            # 日時が正しい範囲内かチェック（例: 2000年以降）
            if pd.notna(min_date) and min_date < pd.Timestamp("2000-01-01"):
                warnings.append(f"start_datetimeの最小値が異常です: {min_date}")
            if pd.notna(max_date) and max_date > pd.Timestamp.now():
                warnings.append(f"start_datetimeの最大値が未来です: {max_date}")

        # 5. データ型検証（簡易版）
        for col_def in schema.get("columns", []):
            col_name = col_def["name"]
            expected_type = col_def.get("type", "numeric")
            if col_name in df.columns:
                actual_dtype = str(df[col_name].dtype)
                # 数値型の簡易チェック
                if expected_type == "numeric" and "int" not in actual_dtype and "float" not in actual_dtype:
                    warnings.append(f"カラム '{col_name}' のデータ型が想定と異なります: 期待=数値型, 実際={actual_dtype}")

        # エラーがある場合は例外を投げる
        if errors:
            error_msg = f"{data_name}の検証に失敗しました:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

        # 警告がある場合はログ出力
        if warnings:
            logger.warning(f"{data_name}の検証で警告があります:")
            for w in warnings:
                logger.warning(f"  - {w}")
        else:
            logger.info(f"{data_name}の検証が完了しました（問題なし）")

