"""
特徴量抽出モジュール
前走データ抽出と統計特徴量計算を担当
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .cache_loader import CacheLoader
from .feature_converter import FeatureConverter


class PreviousRaceExtractor:
    """前走データ抽出クラス。SEDデータから各馬の前走データを抽出。"""

    def __init__(self, cache_loader: CacheLoader):
        """初期化。cache_loader: CacheLoaderインスタンス（生データ取得用）。"""
        self._cache_loader = cache_loader

    def extract(self, df: pd.DataFrame, sed_df: pd.DataFrame) -> pd.DataFrame:
        """SEDデータから前走データを抽出。前走データが追加されたDataFrameを返す。"""
        df = df.copy()

        # 前走データ用のカラムを初期化
        for i in range(1, 6):
            prev_cols = [
                f"prev_{i}_race_num",
                f"prev_{i}_num_horses",
                f"prev_{i}_frame",
                f"prev_{i}_horse_number",
                f"prev_{i}_rank",
                f"prev_{i}_time",
                f"prev_{i}_distance",
                f"prev_{i}_course_type",
                f"prev_{i}_ground_condition",
            ]
            for col in prev_cols:
                if col not in df.columns:
                    df[col] = np.nan

        # 血統登録番号と年月日で前走を検索
        # SEDデータにrace_keyと年月日を追加（BACデータの年月日基準）
        bac_df = self._cache_loader.get_raw_data("BAC")
        sed_df_with_key = self._add_race_key_to_sed_df(sed_df, bac_df)

        # 血統登録番号ごとに過去のレースを時系列でソート
        if "血統登録番号" in df.columns and "race_key" in df.columns:
            # race_keyが存在するSEDデータのみを使用
            sed_df_with_key_filtered = sed_df_with_key[
                sed_df_with_key["race_key"].notna() & sed_df_with_key["血統登録番号"].notna()
            ].copy()

            # race_keyでソート（文字列としてソート、YYYYMMDD形式なので時系列順になる）
            sed_df_with_key_filtered = sed_df_with_key_filtered.sort_values(
                "race_key", ascending=True
            )

            # 各馬の前走データを抽出（並列化）
            import multiprocessing

            n_jobs = max(1, multiprocessing.cpu_count() - 1)

            # 各馬のデータを準備
            horse_ids = [h for h in df["血統登録番号"].unique() if not pd.isna(h)]
            horse_data_list = []
            for horse_id in horse_ids:
                horse_sed = sed_df_with_key_filtered[
                    sed_df_with_key_filtered["血統登録番号"] == horse_id
                ]

                if len(horse_sed) == 0:
                    continue

                horse_main = df[df["血統登録番号"] == horse_id]
                horse_main_indices = horse_main.index.tolist()
                horse_main_race_keys = horse_main["race_key"].tolist()

                horse_data_list.append(
                    (horse_id, horse_main_indices, horse_main_race_keys, horse_sed)
                )

            # 並列処理を実行
            if len(horse_data_list) > 0:
                print(f"前走データ抽出中（並列処理: {n_jobs}コア、{len(horse_data_list)}頭）...")
                # バッチサイズを調整してメモリ使用量を削減
                batch_size = max(100, len(horse_data_list) // (n_jobs * 4))
                all_results = Parallel(n_jobs=n_jobs, batch_size=batch_size, verbose=1)(
                    delayed(self._process_horse_previous_races)(
                        horse_id, horse_main_indices, horse_main_race_keys, horse_sed
                    )
                    for horse_id, horse_main_indices, horse_main_race_keys, horse_sed in horse_data_list
                )

                # 結果を結合してDataFrameに反映（一括更新で高速化）
                prev_cols = [
                    "prev_1_rank", "prev_1_time", "prev_1_distance", "prev_1_num_horses",
                    "prev_1_course_type", "prev_1_ground_condition",
                    "prev_2_rank", "prev_2_time", "prev_2_distance", "prev_2_num_horses",
                    "prev_2_course_type", "prev_2_ground_condition",
                    "prev_3_rank", "prev_3_time", "prev_3_distance", "prev_3_num_horses",
                    "prev_3_course_type", "prev_3_ground_condition",
                    "prev_4_rank", "prev_4_time", "prev_4_distance", "prev_4_num_horses",
                    "prev_4_course_type", "prev_4_ground_condition",
                    "prev_5_rank", "prev_5_time", "prev_5_distance", "prev_5_num_horses",
                    "prev_5_course_type", "prev_5_ground_condition",
                ]
                
                # 結果を辞書にまとめる（インデックス → カラム → 値）
                update_dict = {col: {} for col in prev_cols}
                for horse_results in all_results:
                    for result in horse_results:
                        idx = result["index"]
                        for col in prev_cols:
                            if col in result:
                                update_dict[col][idx] = result[col]
                
                # 一括更新（df.atより大幅に高速）
                for col in prev_cols:
                    if update_dict[col]:
                        df.loc[list(update_dict[col].keys()), col] = pd.Series(update_dict[col])

        return df

    def _process_horse_previous_races(
        self, horse_id, horse_main_indices, horse_main_race_keys, horse_sed_df
    ):
        """
        1頭の馬の前走データを抽出（並列化用）

        Args:
            horse_id: 血統登録番号
            horse_main_indices: メインデータのインデックスリスト
            horse_main_race_keys: メインデータのrace_keyリスト
            horse_sed_df: 該当馬のSEDデータ（race_keyでソート済み）

        Returns:
            前走データの辞書リスト（インデックス、カラム名、値のマッピング）
        """
        results = []

        if len(horse_sed_df) == 0:
            return results

        # race_keyをインデックスとして使用して高速化（文字列比較を避ける）
        # ただし、race_keyが文字列の場合はそのまま使用
        sed_race_keys = horse_sed_df["race_key"].values

        # 各レースに対して前走データを設定
        for idx, current_race_key in zip(horse_main_indices, horse_main_race_keys):
            if not current_race_key:
                continue

            # 現在のレースより前のレースを取得（ベクトル化で高速化）
            # race_keyは文字列なので、比較は避けられないが、NumPy配列での比較は高速
            mask = sed_race_keys < current_race_key
            prev_indices = np.where(mask)[0]
            
            if len(prev_indices) == 0:
                continue

            # 最後の5件を取得（既にソート済みなので、末尾から取得）
            prev_indices = prev_indices[-5:] if len(prev_indices) >= 5 else prev_indices
            prev_races = horse_sed_df.iloc[prev_indices]

            # 前走データを設定（1走前から5走前まで、新しい順）
            # 既に時系列順なので、逆順にする
            prev_races_sorted = prev_races.iloc[::-1]

            result_dict = {"index": idx}
            for i in range(min(5, len(prev_races_sorted))):
                prev_row = prev_races_sorted.iloc[i]
                result_dict[f"prev_{i + 1}_rank"] = prev_row.get("着順", np.nan)
                result_dict[f"prev_{i + 1}_time"] = prev_row.get("タイム", np.nan)
                result_dict[f"prev_{i + 1}_distance"] = prev_row.get("距離", np.nan)
                result_dict[f"prev_{i + 1}_num_horses"] = prev_row.get("頭数", np.nan)
                result_dict[f"prev_{i + 1}_course_type"] = prev_row.get("芝ダ障害コード", np.nan)
                result_dict[f"prev_{i + 1}_ground_condition"] = prev_row.get("馬場状態", np.nan)

            results.append(result_dict)

        return results

    def _add_race_key_to_sed_df(
        self, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """SEDデータにrace_keyを追加"""
        if bac_df is not None:
            return FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
        else:
            return FeatureConverter.add_race_key_to_df(sed_df, use_bac_date=False)


class StatisticalFeatureCalculator:
    """統計特徴量計算クラス。馬・騎手・調教師の過去成績統計を計算。"""

    def __init__(self, cache_loader: CacheLoader):
        """初期化。cache_loader: CacheLoaderインスタンス（生データ取得用）。"""
        self._cache_loader = cache_loader

    def calculate(self, df: pd.DataFrame, sed_df: pd.DataFrame) -> pd.DataFrame:
        """馬・騎手・調教師の過去成績統計特徴量を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
        # dfは後で変更するのでコピーが必要、sed_dfは読み取り専用なのでコピー不要
        df = df.copy()

        # SEDデータにrace_keyと年月日を追加（BACデータの年月日基準）
        bac_df = self._cache_loader.get_raw_data("BAC")
        sed_df_with_key = self._add_race_key_to_sed_df(sed_df, bac_df)

        # dfにstart_datetimeを生成
        df = FeatureConverter.add_start_datetime_to_df(df)

        # 統計量計算用のデータフレームを準備
        stats_df = sed_df_with_key[
            ["race_key", "馬番", "血統登録番号", "騎手コード", "調教師コード", "着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
        ].copy()
        stats_df["rank_1st"] = (stats_df["着順"] == 1).astype(int)
        stats_df["rank_3rd"] = (stats_df["着順"].isin([1, 2, 3])).astype(int)

        # 各レースの開始日時を取得（ベクトル化）
        stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(
            stats_df["race_key"]
        )

        # 馬の統計量（各レースのstart_datetimeより前のデータのみを使用）
        if "血統登録番号" in df.columns:
            horse_stats = self._calculate_time_series_stats_for_targets(
                stats_df, df, "血統登録番号", "start_datetime"
            )
            df = df.merge(
                horse_stats,
                on=["血統登録番号", "start_datetime"],
                how="left",
                suffixes=("", "_horse_stats"),
            )

        # 騎手の統計量と直近3レース詳細（各レースのstart_datetimeより前のデータのみを使用）
        if "騎手コード" in df.columns:
            jockey_stats = self._calculate_time_series_stats_for_targets(
                stats_df, df, "騎手コード", "start_datetime"
            )
            jockey_recent_races = self._extract_recent_races_for_targets(
                stats_df, df, "騎手コード", "start_datetime", num_races=3, prefix="jockey"
            )
            jockey_all = jockey_stats.merge(
                jockey_recent_races,
                on=["騎手コード", "start_datetime"],
                how="left",
            )
            df = df.merge(
                jockey_all,
                on=["騎手コード", "start_datetime"],
                how="left",
                suffixes=("", "_jockey_stats"),
            )

        # 調教師の統計量（各レースのstart_datetimeより前のデータのみを使用）
        if "調教師コード" in df.columns:
            trainer_stats = self._calculate_time_series_stats_for_targets(
                stats_df, df, "調教師コード", "start_datetime"
            )
            df = df.merge(
                trainer_stats,
                on=["調教師コード", "start_datetime"],
                how="left",
                suffixes=("", "_trainer_stats"),
            )

        return df

    def _calculate_time_series_stats_for_targets(
        self, stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータのみを使って統計量を計算（未来情報を完全に除外）。"""
        stats_df = stats_df.sort_values(by=[group_col, time_col])
        target_df = target_df[[group_col, time_col]].copy()

        # カラム名のプレフィックスを決定
        if group_col == "血統登録番号":
            prefix = "horse"
        elif group_col == "騎手コード":
            prefix = "jockey"
        elif group_col == "調教師コード":
            prefix = "trainer"
        else:
            prefix = group_col.replace("コード", "").replace("血統登録番号", "horse")

        # 各レースに対して、そのレースのstart_datetimeより前のデータのみを使って統計量を計算
        def calculate_stats_for_row(row):
            group_value = row[group_col]
            target_datetime = row[time_col]

            # そのレースのstart_datetimeより前のデータのみをフィルタリング
            past_data = stats_df[
                (stats_df[group_col] == group_value) & (stats_df[time_col] < target_datetime)
            ]

            if len(past_data) == 0:
                return pd.Series({
                    f"{prefix}_win_rate": 0.0,
                    f"{prefix}_place_rate": 0.0,
                    f"{prefix}_avg_rank": 0.0,
                    f"{prefix}_race_count": 0,
                })

            win_rate = past_data["rank_1st"].mean() if len(past_data) > 0 else 0.0
            place_rate = past_data["rank_3rd"].mean() if len(past_data) > 0 else 0.0
            avg_rank = past_data["着順"].mean() if len(past_data) > 0 else 0.0
            race_count = len(past_data)

            return pd.Series({
                f"{prefix}_win_rate": win_rate,
                f"{prefix}_place_rate": place_rate,
                f"{prefix}_avg_rank": avg_rank,
                f"{prefix}_race_count": race_count,
            })

        # 各レースに対して統計量を計算
        stats_result = target_df.apply(calculate_stats_for_row, axis=1)
        result_df = pd.concat([target_df, stats_result], axis=1)

        return result_df

    def _extract_recent_races_for_targets(
        self, stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, num_races: int = 3, prefix: str = "jockey"
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータから直近Nレースの詳細情報を抽出（未来情報を完全に除外）。"""
        stats_df = stats_df.sort_values(by=[group_col, time_col])
        target_df = target_df[[group_col, time_col]].copy()

        # 各レースに対して、そのレースのstart_datetimeより前のデータから直近Nレースの詳細を取得
        def extract_recent_races_for_row(row):
            group_value = row[group_col]
            target_datetime = row[time_col]

            # そのレースのstart_datetimeより前のデータのみをフィルタリング
            past_data = stats_df[
                (stats_df[group_col] == group_value) & (stats_df[time_col] < target_datetime)
            ].sort_values(by=time_col, ascending=False)

            result = {}
            # 直近Nレースの詳細情報を取得
            for i in range(1, num_races + 1):
                if len(past_data) >= i:
                    recent_race = past_data.iloc[i - 1]
                    result[f"{prefix}_recent_{i}_rank"] = recent_race.get("着順", np.nan)
                    result[f"{prefix}_recent_{i}_time"] = recent_race.get("タイム", np.nan)
                    result[f"{prefix}_recent_{i}_distance"] = recent_race.get("距離", np.nan)
                    result[f"{prefix}_recent_{i}_course_type"] = recent_race.get("芝ダ障害コード", np.nan)
                    result[f"{prefix}_recent_{i}_ground_condition"] = recent_race.get("馬場状態", np.nan)
                    result[f"{prefix}_recent_{i}_num_horses"] = recent_race.get("頭数", np.nan)
                    result[f"{prefix}_recent_{i}_race_num"] = recent_race.get("R", np.nan)
                else:
                    result[f"{prefix}_recent_{i}_rank"] = np.nan
                    result[f"{prefix}_recent_{i}_time"] = np.nan
                    result[f"{prefix}_recent_{i}_distance"] = np.nan
                    result[f"{prefix}_recent_{i}_course_type"] = np.nan
                    result[f"{prefix}_recent_{i}_ground_condition"] = np.nan
                    result[f"{prefix}_recent_{i}_num_horses"] = np.nan
                    result[f"{prefix}_recent_{i}_race_num"] = np.nan

            return pd.Series(result)

        # 各レースに対して直近Nレースの詳細を抽出
        recent_races_result = target_df.apply(extract_recent_races_for_row, axis=1)
        result_df = pd.concat([target_df, recent_races_result], axis=1)

        return result_df

    def _add_race_key_to_sed_df(
        self, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """SEDデータにrace_keyを追加"""
        if bac_df is not None:
            return FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
        else:
            return FeatureConverter.add_race_key_to_df(sed_df, use_bac_date=False)

