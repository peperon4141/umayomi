"""前走データ抽出クラス。SEDデータから各馬の前走データを抽出。"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
from tqdm import tqdm

from ._03_01_feature_converter import FeatureConverter


class PreviousRaceExtractor:
    """前走データ抽出クラス（staticメソッドのみ）"""

    @staticmethod
    def extract(df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: pd.DataFrame) -> pd.DataFrame:
        """SEDデータから前走データを抽出。前走データが追加されたDataFrameを返す。"""
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        # 前走データを追加するため、元のDataFrameを変更する必要がある
        # main.pyから参照で渡されるため、ここでcopy()が必要
        df = df.copy()  # 前走データを追加するため、コピーが必要
        
        sed_df_with_key = None
        sed_df_with_key_filtered = None
        horse_data_list = None
        all_results = None
        update_dict = None
        
        try:
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
                    f"prev_{i}_race_key",  # 日程情報（リーク検証用）
                ]
                for col in prev_cols:
                    if col not in df.columns:
                        # race_keyは文字列型で初期化
                        if "race_key" in col:
                            df[col] = None  # Noneを使用してobject型にする
                        else:
                            df[col] = np.nan

            # 血統登録番号と年月日で前走を検索
            # SEDデータにrace_keyと年月日を追加（BACデータの年月日基準）
            sed_df_with_key = PreviousRaceExtractor._add_race_key_to_sed_df(sed_df, bac_df)

            # 前走データ抽出の準備
            if "血統登録番号" in df.columns and "race_key" in df.columns:
                # race_keyが存在するSEDデータのみを使用（フィルタリングのみ、コピーは後で必要になったら実行）
                # フィルタリングとソートで新しいDataFrameが作成されるため、明示的なcopy()は不要
                sed_df_with_key_filtered = sed_df_with_key[
                    sed_df_with_key["race_key"].notna() & sed_df_with_key["血統登録番号"].notna()
                ]

                # start_datetimeを追加（時系列比較用）
                if "start_datetime" not in sed_df_with_key_filtered.columns:
                    sed_df_with_key_filtered["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(
                        sed_df_with_key_filtered["race_key"]
                    )

                # 全データを時系列でソート（パフォーマンス最適化のため、1回のソートで全馬のデータを処理）
                # sort_valuesは新しいDataFrameを返すため、明示的なcopy()は不要
                sed_df_with_key_filtered = sed_df_with_key_filtered.sort_values(
                    "start_datetime", ascending=True
                )

                # 各馬の前走データを抽出（シーケンシャル処理）
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
                    
                    # start_datetimeを取得（時系列比較用）
                    if "start_datetime" not in horse_main.columns:
                        # SettingWithCopyWarningを避けるため、.locを使用
                        df.loc[horse_main.index, "start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(
                            horse_main["race_key"]
                        )
                        horse_main = df.loc[horse_main.index]  # 更新後のデータを取得
                    horse_main_datetimes = horse_main["start_datetime"].tolist()

                    horse_data_list.append(
                        (horse_id, horse_main_indices, horse_main_race_keys, horse_sed, horse_main_datetimes)
                    )

                # 並列処理で高速化（各馬の処理は独立しているため並列化可能）
                if len(horse_data_list) > 0:
                    # 環境変数DATA_PROCESSER_MAX_WORKERSが設定されていない場合のデフォルト値
                    # デフォルト値4は、CPUコア数に応じて調整可能なオプショナルな設定値
                    # パフォーマンスチューニングのため、環境変数で上書き可能
                    max_workers = int(os.environ.get("DATA_PROCESSER_MAX_WORKERS", "4"))
                    print(f"[_03_02_] 前走データ抽出中（並列処理、{len(horse_data_list)}頭、ワーカー数: {max_workers}）...")
                    all_results = []
                    
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(PreviousRaceExtractor._process_horse_previous_races, horse_id, horse_main_indices, horse_main_race_keys, horse_sed, horse_main_datetimes): horse_id
                            for horse_id, horse_main_indices, horse_main_race_keys, horse_sed, horse_main_datetimes in horse_data_list
                        }
                        
                        # 進捗バーを表示
                        with tqdm(total=len(futures), desc="前走データ抽出", leave=True, unit="頭") as pbar:
                            for future in as_completed(futures):
                                try:
                                    result = future.result()
                                    all_results.append(result)
                                    pbar.update(1)
                                except Exception as e:
                                    horse_id = futures[future]
                                    print(f"[_03_02_] 馬ID {horse_id} の処理でエラー: {e}")
                                    raise

                    # 結果を結合してDataFrameに反映（一括更新で高速化）
                    prev_cols = [
                        "prev_1_rank", "prev_1_time", "prev_1_distance", "prev_1_num_horses",
                        "prev_1_course_type", "prev_1_ground_condition", "prev_1_race_key",
                        "prev_2_rank", "prev_2_time", "prev_2_distance", "prev_2_num_horses",
                        "prev_2_course_type", "prev_2_ground_condition", "prev_2_race_key",
                        "prev_3_rank", "prev_3_time", "prev_3_distance", "prev_3_num_horses",
                        "prev_3_course_type", "prev_3_ground_condition", "prev_3_race_key",
                        "prev_4_rank", "prev_4_time", "prev_4_distance", "prev_4_num_horses",
                        "prev_4_course_type", "prev_4_ground_condition", "prev_4_race_key",
                        "prev_5_rank", "prev_5_time", "prev_5_distance", "prev_5_num_horses",
                        "prev_5_course_type", "prev_5_ground_condition", "prev_5_race_key",
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
                            # race_keyカラムは文字列型として扱う
                            if "race_key" in col:
                                df.loc[list(update_dict[col].keys()), col] = pd.Series(update_dict[col], dtype=object)
                            else:
                                df.loc[list(update_dict[col].keys()), col] = pd.Series(update_dict[col])
            
            return df
        finally:
            # クリーンアップ: 不要なデータを削除
            if sed_df_with_key is not None:
                del sed_df_with_key
            if sed_df_with_key_filtered is not None:
                del sed_df_with_key_filtered
            if horse_data_list is not None:
                del horse_data_list
            if all_results is not None:
                del all_results
            if update_dict is not None:
                del update_dict
            import gc
            gc.collect()

    @staticmethod
    def _process_horse_previous_races(
        horse_id, horse_main_indices, horse_main_race_keys, horse_sed_df, horse_main_datetimes
    ):
        """1頭の馬の前走データを抽出（並列化用）"""
        results = []

        if len(horse_sed_df) == 0:
            return results

        # start_datetimeとrace_keyをインデックスとして使用して高速化（数値比較で正確）
        sed_datetimes = horse_sed_df["start_datetime"].values
        sed_race_keys = horse_sed_df["race_key"].values

        # 各レースに対して前走データを設定
        for idx, current_race_key, current_datetime in zip(horse_main_indices, horse_main_race_keys, horse_main_datetimes):
            if not current_race_key or pd.isna(current_datetime) or current_datetime == 0:
                continue

            # 現在のレースより前のレースを取得（start_datetimeで比較、ベクトル化で高速化）
            # 同じレースキーは除外（同じレースが前走として設定されるのを防ぐ）
            datetime_mask = sed_datetimes < current_datetime
            race_key_mask = sed_race_keys != current_race_key
            mask = datetime_mask & race_key_mask
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
                result_dict[f"prev_{i + 1}_race_key"] = prev_row.get("race_key", np.nan)  # 日程情報（リーク検証用）

            results.append(result_dict)

        return results

    @staticmethod
    def _add_race_key_to_sed_df(
        sed_df: pd.DataFrame, bac_df: pd.DataFrame
    ) -> pd.DataFrame:
        """SEDデータにrace_keyを追加"""
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        return FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
