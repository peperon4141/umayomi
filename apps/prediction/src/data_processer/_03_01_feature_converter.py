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
        
        注意: デフォルト値0を使用する理由
        - この関数はデータ変換時の安全な処理を目的としており、
          不正な値や変換不可能な値が存在する場合でも処理を続行する必要がある
        - デフォルト値0は「変換不可能な値」を表すマーカーとして使用される
        - データ不整合の可能性がある場合は、呼び出し側で事前に検証することを推奨
        """
        if value is None:
            return default
        try:
            if pd.isna(value):
                return default
        except (TypeError, ValueError):
            pass
        if isinstance(value, (int, float)):
            if isinstance(value, float) and (value != value):  # NaNチェック
                return default
            try:
                return int(value)
            except (ValueError, OverflowError):
                return default
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def safe_ymd(value) -> str:
        """年月日フィールドを安全に処理（数値や文字列から8桁の文字列を取得）"""
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        if isinstance(value, (int, float)):
            if isinstance(value, float) and (value != value):
                return ""
            try:
                ymd_int = int(value)
                return str(ymd_int).zfill(8)
            except (ValueError, OverflowError):
                return ""
        ymd_str = str(value).replace(".0", "").replace(".", "")
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
        """レースキーを生成（年月日+場コード+回+日+R）"""
        date_str = f"{year:04d}{month:02d}{day:02d}"
        place_code_int = FeatureConverter.safe_int(place_code) if place_code else 0
        place_str = f"{place_code_int:02d}"
        round_str = f"{int(kaisai_round):02d}"
        day_str = str(kaisai_day).lower()
        race_str = f"{int(race_number):02d}"
        return f"{date_str}_{place_str}_{round_str}_{day_str}_{race_str}"

    @staticmethod
    def extract_ymd_from_value(ymd_value, year_value=None) -> tuple[int, int, int]:
        """年月日フィールドから年・月・日を抽出"""
        ymd = FeatureConverter.safe_ymd(ymd_value)
        if len(ymd) == 8:
            year = int(ymd[:4])
            month = int(ymd[4:6])
            day = int(ymd[6:8])
        else:
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
        """DataFrameから年月日を抽出（ベクトル化版）"""
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

        year = pd.Series(2024, index=df.index, dtype="int64")
        month = pd.Series(1, index=df.index, dtype="int64")
        day = pd.Series(1, index=df.index, dtype="int64")

        if mask_primary.any():
            year.loc[mask_primary] = ymd_str_primary.loc[mask_primary].str[:4].astype(int)
            month.loc[mask_primary] = ymd_str_primary.loc[mask_primary].str[4:6].astype(int)
            day.loc[mask_primary] = ymd_str_primary.loc[mask_primary].str[6:8].astype(int)

        if mask_fallback.any():
            mask_fallback_only = mask_fallback & ~mask_primary
            if mask_fallback_only.any():
                year.loc[mask_fallback_only] = ymd_str.loc[mask_fallback_only].str[:4].astype(int)
                month.loc[mask_fallback_only] = ymd_str.loc[mask_fallback_only].str[4:6].astype(int)
                day.loc[mask_fallback_only] = ymd_str.loc[mask_fallback_only].str[6:8].astype(int)

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
        """BACデータから年月日マッピングを作成（場コード、回、日、R）-> 年月日"""
        # 必要なカラムのみを抽出してメモリ使用量を削減
        required_cols = ["場コード", "回", "日", "R", "年月日"]
        bac_df_subset = bac_df[required_cols].copy()
        bac_df_subset["key"] = (
            bac_df_subset["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df_subset["回"].fillna(1).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df_subset["日"].fillna("1").astype(str).str.lower()
            + "_"
            + bac_df_subset["R"].fillna(1).astype(int).astype(str).str.zfill(2)
        )
        bac_df_subset["ymd"] = bac_df_subset["年月日"].apply(FeatureConverter.safe_ymd)
        bac_df_filtered = bac_df_subset[bac_df_subset["ymd"].str.len() == 8]

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
        """BACデータから年月日マッピングを作成（マージ用DataFrame形式）"""
        # 必要なカラムのみを抽出してメモリ使用量を削減
        required_cols = ["場コード", "回", "日", "R", "年月日"]
        bac_df_subset = bac_df[required_cols].copy()
        bac_df_subset["key"] = (
            bac_df_subset["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df_subset["回"].fillna(1).astype(int).astype(str).str.zfill(2)
            + "_"
            + bac_df_subset["日"].fillna("1").astype(str).str.lower()
            + "_"
            + bac_df_subset["R"].fillna(1).astype(int).astype(str).str.zfill(2)
        )
        bac_df_subset["ymd"] = bac_df_subset["年月日"].apply(FeatureConverter.safe_ymd)
        bac_df_filtered = bac_df_subset[bac_df_subset["ymd"].str.len() == 8]

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
        """race_keyを生成（ベクトル化版）"""
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
        """DataFrameにrace_keyを追加（統一化版）"""
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()
        bac_mapping_df = None
        
        try:
            if use_bac_date and bac_df is not None:
                bac_mapping_df = FeatureConverter.create_bac_date_mapping_for_merge(bac_df)
                df["key"] = (
                    df["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
                    + "_"
                    + df["回"].fillna(1).astype(int).astype(str).str.zfill(2)
                    + "_"
                    + df["日"].fillna("1").astype(str).str.lower()
                    + "_"
                    + df["R"].fillna(1).astype(int).astype(str).str.zfill(2)
                )
                df = df.merge(bac_mapping_df, on="key", how="left", suffixes=("", "_bac"))
                year, month, day = FeatureConverter.extract_ymd_from_df_vectorized(
                    df, ymd_col="ymd", year_col="年", ymd_fallback_col="年月日"
                )
                df = df.drop(columns=["key", "ymd"], errors="ignore")
            else:
                year, month, day = FeatureConverter.extract_ymd_from_df_vectorized(
                    df, ymd_col="年月日", year_col="年"
                )

            df["race_key"] = FeatureConverter.generate_race_key_vectorized(
                year, month, day, df["場コード"], df["回"], df["日"], df["R"]
            )

            return df
        finally:
            # クリーンアップ: 不要なデータを削除
            if bac_mapping_df is not None:
                del bac_mapping_df
            import gc
            gc.collect()

    @staticmethod
    def get_datetime_from_race_key(race_key: str) -> int:
        """race_keyからstart_datetimeを取得（単一値用）"""
        if not race_key or not isinstance(race_key, str):
            return 0
        try:
            date_str = race_key.split("_")[0]
            if len(date_str) == 8:
                return int(date_str) * 10000
        except Exception:
            pass
        return 0

    @staticmethod
    def get_datetime_from_race_key_vectorized(race_key_series: pd.Series) -> pd.Series:
        """race_keyからstart_datetimeを取得（ベクトル化版）"""
        date_str = race_key_series.astype(str).str.split("_").str[0]
        mask = date_str.str.len() == 8
        result = pd.Series(0, index=race_key_series.index, dtype="int64")
        result.loc[mask] = date_str[mask].astype(int) * 10000
        return result

    @staticmethod
    def convert_sed_time_to_seconds(time_val) -> float:
        """SEDデータのタイム形式を秒に変換"""
        if pd.isna(time_val):
            return np.nan
        try:
            time_int = int(time_val)
            minutes = time_int // 1000
            seconds_deci = time_int % 1000
            return minutes * 60 + seconds_deci / 10.0
        except (ValueError, TypeError):
            return np.nan

    @staticmethod
    def add_start_datetime_to_df(df: pd.DataFrame) -> pd.DataFrame:
        """DataFrameにstart_datetimeを追加（統一化）"""
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()
        
        try:
            if "start_datetime" in df.columns:
                return df

            if "年月日" in df.columns and "発走時間" in df.columns:
                ymd_str = df["年月日"].fillna(0).astype(int).astype(str).str.zfill(8)
                time_str = df["発走時間"].fillna(0).astype(int).astype(str).str.zfill(4)
                mask = df["年月日"].notna() & df["発走時間"].notna()
                df["start_datetime"] = (ymd_str + time_str).astype(int)
                df.loc[~mask, "start_datetime"] = 0
            elif "年月日" in df.columns:
                ymd_str = df["年月日"].fillna(0).astype(int).astype(str).str.zfill(8)
                df["start_datetime"] = ymd_str.astype(int) * 10000
                df.loc[df["年月日"].isna(), "start_datetime"] = 0
            elif "race_key" in df.columns:
                df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(
                    df["race_key"]
                )
            else:
                df["start_datetime"] = 0

            return df
        finally:
            # この関数内で作成された中間変数は自動的に削除される
            # 必要に応じて明示的に削除
            import gc
            gc.collect()

