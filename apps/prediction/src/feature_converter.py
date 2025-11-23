"""
特徴量変換ユーティリティ
race_key生成、年月日処理などの変換処理を統一化
"""

from typing import Optional, Union

import numpy as np
import pandas as pd


class FeatureConverter:
    """
    特徴量変換を担当するユーティリティクラス
    race_key生成、年月日処理などを統一化
    """

    @staticmethod
    def safe_int(value, default: int = 0) -> int:
        """
        安全に数値に変換するヘルパー関数

        Args:
            value: 変換対象の値
            default: 変換失敗時のデフォルト値

        Returns:
            変換された整数値
        """
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return int(value)
        try:
            # 文字列の場合、float経由で変換（'6.0' -> 6）
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_ymd(value) -> str:
        """
        年月日フィールドを安全に処理（数値や文字列から8桁の文字列を取得）

        Args:
            value: 年月日フィールドの値

        Returns:
            8桁の年月日文字列（例: "20241102"）
        """
        if value is None:
            return ""
        # NaNの処理（pd.isnaはNone、NaN、NaTなどすべてを検出）
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            # pd.isnaが使えない型（例：文字列）の場合はスキップ
            pass
        # 数値の場合は整数に変換してから文字列に
        if isinstance(value, (int, float)):
            # NaNチェック（数値型の場合のみ）
            if isinstance(value, float) and (value != value):  # NaNは自分自身と等しくない
                return ""
            try:
                ymd_int = int(value)
                return str(ymd_int).zfill(8)
            except (ValueError, OverflowError):
                return ""
        # 文字列の場合
        ymd_str = str(value).replace(".0", "").replace(".", "")
        # 小数点以下を除去
        if "." in ymd_str:
            ymd_str = ymd_str.split(".")[0]
        return ymd_str.zfill(8)

    @staticmethod
    def generate_race_key(
        year: int,
        month: int,
        day: int,
        place_code: Union[str, int],
        kaisai_round: int,
        kaisai_day: str,
        race_number: int,
    ) -> str:
        """
        レースキーを生成（年月日+場コード+回+日+R）

        Args:
            year: 年
            month: 月
            day: 日
            place_code: 場コード（文字列または数値）
            kaisai_round: 回
            kaisai_day: 日（16進数）
            race_number: R（レース番号）

        Returns:
            レースキー（例: "20241102_01_1_a_01"）
        """
        date_str = f"{year:04d}{month:02d}{day:02d}"
        # place_codeが文字列（'6.0'など）の場合も対応
        place_code_int = FeatureConverter.safe_int(place_code) if place_code else 0
        place_str = f"{place_code_int:02d}"
        round_str = f"{int(kaisai_round):02d}"
        day_str = str(kaisai_day).lower()
        race_str = f"{int(race_number):02d}"
        return f"{date_str}_{place_str}_{round_str}_{day_str}_{race_str}"

    @staticmethod
    def extract_ymd_from_value(ymd_value, year_value=None) -> tuple[int, int, int]:
        """
        年月日フィールドから年・月・日を抽出

        Args:
            ymd_value: 年月日フィールドの値
            year_value: 年フィールドの値（フォールバック用）

        Returns:
            (year, month, day) のタプル
        """
        ymd = FeatureConverter.safe_ymd(ymd_value)
        if len(ymd) == 8:
            year = int(ymd[:4])
            month = int(ymd[4:6])
            day = int(ymd[6:8])
        else:
            # フォールバック: 年フィールドから
            if year_value is not None:
                year_val = FeatureConverter.safe_int(year_value)
                if year_val > 0:
                    year = year_val + 2000 if year_val < 100 else year_val
                else:
                    year = 2024
            else:
                year = 2024
            month = 1
            day = 1
        return year, month, day

    @staticmethod
    def extract_ymd_from_df_vectorized(
        df: pd.DataFrame,
        ymd_col: str = "年月日",
        year_col: Optional[str] = None,
        ymd_fallback_col: Optional[str] = None,
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """
        DataFrameから年月日を抽出（ベクトル化版）

        Args:
            df: 対象のDataFrame
            ymd_col: 年月日カラム名
            year_col: 年カラム名（フォールバック用）
            ymd_fallback_col: フォールバック用の年月日カラム名

        Returns:
            (year, month, day) のタプル（各要素はpd.Series）
        """
        # 年月日を抽出（ベクトル化）
        if ymd_fallback_col and ymd_fallback_col in df.columns:
            ymd_str = df[ymd_fallback_col].apply(FeatureConverter.safe_ymd)
            mask_fallback = ymd_str.str.len() == 8
        else:
            ymd_str = pd.Series("", index=df.index)
            mask_fallback = pd.Series(False, index=df.index)

        if ymd_col in df.columns:
            ymd_str_primary = df[ymd_col].apply(FeatureConverter.safe_ymd)
            mask_primary = ymd_str_primary.str.len() == 8
        else:
            ymd_str_primary = pd.Series("", index=df.index)
            mask_primary = pd.Series(False, index=df.index)

        # 年月日から年・月・日を抽出（ベクトル化）
        year = pd.Series(2024, index=df.index, dtype="int64")
        month = pd.Series(1, index=df.index, dtype="int64")
        day = pd.Series(1, index=df.index, dtype="int64")

        # プライマリソースから抽出
        if mask_primary.any():
            year.loc[mask_primary] = ymd_str_primary.loc[mask_primary].str[:4].astype(int)
            month.loc[mask_primary] = ymd_str_primary.loc[mask_primary].str[4:6].astype(int)
            day.loc[mask_primary] = ymd_str_primary.loc[mask_primary].str[6:8].astype(int)

        # フォールバックソースから抽出
        if mask_fallback.any():
            mask_fallback_only = mask_fallback & ~mask_primary
            if mask_fallback_only.any():
                year.loc[mask_fallback_only] = ymd_str.loc[mask_fallback_only].str[:4].astype(int)
                month.loc[mask_fallback_only] = ymd_str.loc[mask_fallback_only].str[4:6].astype(int)
                day.loc[mask_fallback_only] = ymd_str.loc[mask_fallback_only].str[6:8].astype(int)

        # 年フィールドからフォールバック
        if year_col and year_col in df.columns:
            mask_no_date = ~mask_primary & ~mask_fallback
            if mask_no_date.any():
                year_vals = df.loc[mask_no_date, year_col].apply(FeatureConverter.safe_int)
                year.loc[mask_no_date] = year_vals.apply(
                    lambda y: y + 2000 if y < 100 else y if y > 0 else 2024
                )

        return year, month, day

    @staticmethod
    def create_bac_date_mapping(bac_df: pd.DataFrame) -> dict[tuple, str]:
        """
        BACデータから年月日マッピングを作成
        （場コード、回、日、R）-> 年月日

        Args:
            bac_df: BACデータのDataFrame

        Returns:
            マッピング辞書
        """
        bac_df = bac_df.copy()

        # キーを生成（ベクトル化）
        bac_df["key"] = (
            bac_df["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df["回"].fillna(1).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df["日"].fillna("1").astype(str).str.lower()
            + "_"
            + bac_df["R"].fillna(1).astype(int).astype(str).str.zfill(2)
        )
        bac_df["ymd"] = bac_df["年月日"].apply(FeatureConverter.safe_ymd)
        bac_df_filtered = bac_df[bac_df["ymd"].str.len() == 8].copy()

        # マッピングを作成
        date_map = {}
        for _, row in bac_df_filtered.iterrows():
            key = (
                FeatureConverter.safe_int(row["場コード"]),
                FeatureConverter.safe_int(row["回"]),
                str(row["日"]).lower(),
                FeatureConverter.safe_int(row["R"]),
            )
            date_map[key] = row["ymd"]

        return date_map

    @staticmethod
    def create_bac_date_mapping_for_merge(bac_df: pd.DataFrame) -> pd.DataFrame:
        """
        BACデータから年月日マッピングを作成（マージ用DataFrame形式）

        Args:
            bac_df: BACデータのDataFrame

        Returns:
            keyとymdカラムを持つDataFrame
        """
        bac_df = bac_df.copy()

        # キーを生成（ベクトル化）
        bac_df["key"] = (
            bac_df["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df["回"].fillna(1).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df["日"].fillna("1").astype(str).str.lower()
            + "_"
            + bac_df["R"].fillna(1).astype(int).astype(str).str.zfill(2)
        )
        bac_df["ymd"] = bac_df["年月日"].apply(FeatureConverter.safe_ymd)
        bac_df_filtered = bac_df[bac_df["ymd"].str.len() == 8].copy()

        return bac_df_filtered[["key", "ymd"]]

    @staticmethod
    def generate_race_key_vectorized(
        year: pd.Series,
        month: pd.Series,
        day: pd.Series,
        place_code: pd.Series,
        kaisai_round: pd.Series,
        kaisai_day: pd.Series,
        race_number: pd.Series,
    ) -> pd.Series:
        """
        race_keyを生成（ベクトル化版）

        Args:
            year: 年のSeries
            month: 月のSeries
            day: 日のSeries
            place_code: 場コードのSeries
            kaisai_round: 回のSeries
            kaisai_day: 日のSeries（16進数）
            race_number: RのSeries

        Returns:
            race_keyのSeries
        """
        date_str = (
            year.astype(str).str.zfill(4)
            + month.astype(str).str.zfill(2)
            + day.astype(str).str.zfill(2)
        )
        place_code_str = place_code.fillna(0).astype(int).astype(str).str.zfill(2)
        round_str = kaisai_round.fillna(1).astype(int).astype(str).str.zfill(2)
        day_str = kaisai_day.fillna("1").astype(str).str.lower()
        race_str = race_number.fillna(1).astype(int).astype(str).str.zfill(2)

        return date_str + "_" + place_code_str + "_" + round_str + "_" + day_str + "_" + race_str

    @staticmethod
    def add_race_key_to_df(
        df: pd.DataFrame, bac_df: Optional[pd.DataFrame] = None, use_bac_date: bool = True
    ) -> pd.DataFrame:
        """
        DataFrameにrace_keyを追加（統一化版）

        Args:
            df: 対象のDataFrame
            bac_df: BACデータ（年月日を取得するため、オプション）
            use_bac_date: BACデータから年月日を取得するかどうか

        Returns:
            race_keyが追加されたDataFrame
        """
        df = df.copy()

        # BACデータから年月日を取得する必要がある場合
        if use_bac_date and bac_df is not None:
            # BACデータから年月日マッピングを作成
            bac_mapping_df = FeatureConverter.create_bac_date_mapping_for_merge(bac_df)

            # キーを生成
            df["key"] = (
                df["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
                + "_"
                + df["回"].fillna(1).astype(int).astype(str).str.zfill(2)
                + "_"
                + df["日"].fillna("1").astype(str).str.lower()
                + "_"
                + df["R"].fillna(1).astype(int).astype(str).str.zfill(2)
            )

            # BACデータから年月日を取得（マージ）
            df = df.merge(bac_mapping_df, on="key", how="left", suffixes=("", "_bac"))

            # 年月日を抽出（ベクトル化）
            year, month, day = FeatureConverter.extract_ymd_from_df_vectorized(
                df, ymd_col="ymd", year_col="年", ymd_fallback_col="年月日"
            )

            # 一時カラムを削除
            df = df.drop(columns=["key", "ymd"], errors="ignore")
        else:
            # 年月日を抽出（ベクトル化）
            year, month, day = FeatureConverter.extract_ymd_from_df_vectorized(
                df, ymd_col="年月日", year_col="年"
            )

        # race_keyを生成（ベクトル化）
        df["race_key"] = FeatureConverter.generate_race_key_vectorized(
            year, month, day, df["場コード"], df["回"], df["日"], df["R"]
        )

        return df

    @staticmethod
    def get_datetime_from_race_key(race_key: str) -> int:
        """
        race_keyからstart_datetimeを取得（単一値用）

        Args:
            race_key: レースキー

        Returns:
            start_datetime（YYYYMMDDHHMM形式の数値、発走時間がない場合は0時として扱う）
        """
        if not race_key or not isinstance(race_key, str):
            return 0
        try:
            # race_key形式: YYYYMMDD_場コード_回_日_R
            date_str = race_key.split("_")[0]
            if len(date_str) == 8:
                return int(date_str) * 10000  # 発走時間がない場合は0時として扱う
        except Exception:
            pass
        return 0

    @staticmethod
    def get_datetime_from_race_key_vectorized(race_key_series: pd.Series) -> pd.Series:
        """
        race_keyからstart_datetimeを取得（ベクトル化版）

        Args:
            race_key_series: race_keyのSeries

        Returns:
            start_datetimeのSeries
        """
        # race_keyから年月日部分を一括抽出
        date_str = race_key_series.astype(str).str.split("_").str[0]

        # 8桁の文字列を数値に変換（一括処理）
        mask = date_str.str.len() == 8
        result = pd.Series(0, index=race_key_series.index, dtype="int64")
        result.loc[mask] = date_str[mask].astype(int) * 10000

        return result

    @staticmethod
    def convert_sed_time_to_seconds(time_val) -> float:
        """
        SEDデータのタイム形式を秒に変換
        SED形式: 1byte:分, 2-4byte:秒(0.1秒単位)
        例: 1305 -> 1分30.5秒 -> 90.5秒

        Args:
            time_val: SED形式のタイム値

        Returns:
            秒単位のタイム（float）
        """
        if pd.isna(time_val):
            return np.nan
        try:
            time_int = int(time_val)
            # 1バイト目が分、2-4バイト目が秒（0.1秒単位）
            minutes = time_int // 1000
            seconds_deci = time_int % 1000
            return minutes * 60 + seconds_deci / 10.0
        except (ValueError, TypeError):
            return np.nan

    @staticmethod
    def add_start_datetime_to_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameにstart_datetimeを追加（統一化）

        Args:
            df: 対象のDataFrame

        Returns:
            start_datetimeが追加されたDataFrame
        """
        df = df.copy()

        if "start_datetime" in df.columns:
            return df

        if "年月日" in df.columns and "発走時間" in df.columns:
            # 年月日と発走時間から生成
            ymd_str = df["年月日"].fillna(0).astype(int).astype(str).str.zfill(8)
            time_str = df["発走時間"].fillna(0).astype(int).astype(str).str.zfill(4)
            mask = df["年月日"].notna() & df["発走時間"].notna()
            df["start_datetime"] = (ymd_str + time_str).astype(int)
            df.loc[~mask, "start_datetime"] = 0
        elif "年月日" in df.columns:
            # 年月日のみから生成
            ymd_str = df["年月日"].fillna(0).astype(int).astype(str).str.zfill(8)
            df["start_datetime"] = ymd_str.astype(int) * 10000
            df.loc[df["年月日"].isna(), "start_datetime"] = 0
        elif "race_key" in df.columns:
            # race_keyから生成
            df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(
                df["race_key"]
            )
        else:
            df["start_datetime"] = 0

        return df
