"""統計特徴量計算クラス。馬・騎手・調教師の過去成績統計を計算。"""

import sys
from typing import Optional

import pandas as pd

from .feature_converter import FeatureConverter
from .horse_statistics import HorseStatistics
from .jockey_statistics import JockeyStatistics
from .trainer_statistics import TrainerStatistics


def calculate(df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """馬・騎手・調教師の過去成績統計特徴量を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
    df = df.copy()

    # SEDデータにrace_keyと年月日を追加（BACデータの年月日基準）
    sed_df_with_key = _add_race_key_to_sed_df(sed_df, bac_df)

    # dfにstart_datetimeを生成
    df = FeatureConverter.add_start_datetime_to_df(df)

    # 統計量計算用のデータフレームを準備
    stats_df = sed_df_with_key[
        ["race_key", "馬番", "血統登録番号", "騎手コード", "調教師コード", "着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
    ].copy()
    del sed_df_with_key  # 使用済みのため削除
    stats_df["rank_1st"] = (stats_df["着順"] == 1).astype(int)
    stats_df["rank_3rd"] = (stats_df["着順"].isin([1, 2, 3])).astype(int)

    # 各レースの開始日時を取得（ベクトル化）
    stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(
        stats_df["race_key"]
    )

    # 馬の統計量
    print("馬の統計量を計算中...")
    sys.stdout.flush()
    df = HorseStatistics.calculate(stats_df, df)

    # 騎手の統計量と直近3レース詳細
    print("騎手の統計量を計算中...")
    sys.stdout.flush()
    df = JockeyStatistics.calculate(stats_df, df)

    # 調教師の統計量
    print("調教師の統計量を計算中...")
    sys.stdout.flush()
    df = TrainerStatistics.calculate(stats_df, df)

    del stats_df  # 使用済みのため削除
    return df


def _add_race_key_to_sed_df(
    sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """SEDデータにrace_keyを追加"""
    if bac_df is not None:
        return FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
    else:
        return FeatureConverter.add_race_key_to_df(sed_df, use_bac_date=False)
