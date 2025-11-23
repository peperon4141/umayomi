"""前走データ抽出クラス。SEDデータから各馬の前走データを抽出。"""

from typing import Optional

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .feature_converter import FeatureConverter


def extract(df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
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
    sed_df_with_key = _add_race_key_to_sed_df(sed_df, bac_df)

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
                delayed(_process_horse_previous_races)(
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
    horse_id, horse_main_indices, horse_main_race_keys, horse_sed_df
):
    """1頭の馬の前走データを抽出（並列化用）"""
    results = []

    if len(horse_sed_df) == 0:
        return results

    # race_keyをインデックスとして使用して高速化（文字列比較を避ける）
    sed_race_keys = horse_sed_df["race_key"].values

    # 各レースに対して前走データを設定
    for idx, current_race_key in zip(horse_main_indices, horse_main_race_keys):
        if not current_race_key:
            continue

        # 現在のレースより前のレースを取得（ベクトル化で高速化）
        mask = sed_race_keys < current_race_key
        prev_indices = np.where(mask)[0]
        
        if len(prev_indices) == 0:
            continue

        # 最後の5件を取得（既にソート済みなので、末尾から取得）
        prev_indices = prev_indices[-5:] if len(prev_indices) >= 5 else prev_indices
        prev_races = horse_sed_df.iloc[prev_indices]

        # 前走データを設定（1走前から5走前まで、新しい順）
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
    sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame]
) -> pd.DataFrame:
    """SEDデータにrace_keyを追加"""
    if bac_df is not None:
        return FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
    else:
        return FeatureConverter.add_race_key_to_df(sed_df, use_bac_date=False)
