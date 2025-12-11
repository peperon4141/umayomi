"""前走データ抽出クラス。SEDデータから各馬の前走データを抽出。"""

import gc

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.utils.schema_loader import Schema


class PreviousRaceExtractor:
    """前走データ抽出クラス（staticメソッドのみ）"""
    
    # 結合キー
    MERGE_KEYS = ["race_key", "馬番"]
    
    # 前走データカラム
    PREV_RACE_COLUMNS = ["着順", "タイム", "距離", "頭数", "芝ダ障害コード", "馬場状態", "R"]
    
    # グループ化カラム
    GROUP_COLUMN_HORSE = "血統登録番号"
    
    # 前走データ数
    PREV_RACES_COUNT = 5
    
    # 前走データカラム名のベース（日本語、後で英語に変換される）
    _PREV_COLUMN_BASES = ["着順", "タイム", "距離", "頭数", "芝ダ障害コード", "馬場状態", "race_key", "枠番", "R", "馬番"]

    @staticmethod
    def extract(target_df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
        """結合済みDataFrameから前走データを抽出。前走データが追加されたDataFrameを返す。"""
        target_df = target_df.copy()
        
        try:
            # target_dfに存在する前走データカラムを取得（結合済みデータなので、存在するカラムのみ抽出）
            prev_race_columns = {col: True for col in PreviousRaceExtractor.PREV_RACE_COLUMNS if col in target_df.columns}
            
            # 前走データ抽出用の全データを準備（race_keyがインデックスに設定されている場合はreset_index）
            target_df_for_extract = target_df.reset_index() if isinstance(target_df.index, pd.MultiIndex) and "race_key" in target_df.index.names else target_df
            all_races_df = target_df_for_extract[target_df_for_extract["race_key"].notna() & target_df_for_extract["血統登録番号"].notna()].copy()
            # 全データを時系列でソート
            all_races_df = all_races_df.sort_values("start_datetime", ascending=True)
            
            # 前走データカラム名のリストを生成（日本語、後で英語に変換される）
            prev_cols = [f"前走{i}_{base}" if base != "race_key" else f"前走{i}レースキー_SED" for i in range(1, PreviousRaceExtractor.PREV_RACES_COUNT + 1) for base in PreviousRaceExtractor._PREV_COLUMN_BASES]
            result_dfs = []
            
            # groupbyで各馬ごとに前走データを抽出
            for horse_id, group_df in tqdm(target_df.groupby(PreviousRaceExtractor.GROUP_COLUMN_HORSE), desc="前走データ抽出", unit="頭"):
                if pd.isna(horse_id): continue
                
                # 該当馬の全レースデータを抽出（前走検索用）
                horse_all_races = all_races_df[all_races_df[PreviousRaceExtractor.GROUP_COLUMN_HORSE] == horse_id]
                if len(horse_all_races) == 0: continue
                
                # ベクトル化処理のため配列として取得
                all_races_datetimes = horse_all_races["start_datetime"].values
                all_races_keys = horse_all_races["race_key"].values
                
                # 結果を格納するDataFrameを初期化
                result_data = {col: [] for col in prev_cols}
                result_indices = []
                
                # group_dfがMultiIndexの場合はreset_indexしてから処理
                group_df_for_iter = group_df.reset_index() if isinstance(group_df.index, pd.MultiIndex) else group_df
                original_indices = list(group_df.index) if isinstance(group_df.index, pd.MultiIndex) else list(group_df_for_iter.index)
                
                # 各レースに対して前走データを設定
                for original_idx, (_, row) in zip(original_indices, group_df_for_iter.iterrows()):
                    if "race_key" not in row.index: raise ValueError(f"group_df_for_iterに'race_key'カラムが存在しません。カラム: {list(row.index)[:10]}")
                    current_race_key = row["race_key"]
                    current_datetime = row["start_datetime"]
                    
                    if not current_race_key or pd.isna(current_datetime) or current_datetime == 0:
                        continue

                    # 現在のレースより前のレースを取得（start_datetimeで比較、同じレースキーは除外）
                    datetime_mask = all_races_datetimes < current_datetime
                    race_key_mask = all_races_keys != current_race_key
                    prev_indices = np.where(datetime_mask & race_key_mask)[0]
                    
                    if len(prev_indices) == 0:
                        result_indices.append(original_idx)
                        for col in prev_cols: result_data[col].append(None)
                        continue
                    
                    # 最後のN件を取得（既にソート済みなので、末尾から取得）
                    prev_indices = prev_indices[-PreviousRaceExtractor.PREV_RACES_COUNT:] if len(prev_indices) >= PreviousRaceExtractor.PREV_RACES_COUNT else prev_indices
                    # 前走データを設定（1走前からN走前まで、新しい順）
                    prev_races_sorted = horse_all_races.iloc[prev_indices].iloc[::-1]
                    
                    # 前走データを辞書に格納
                    row_data = {}
                    for i in range(min(PreviousRaceExtractor.PREV_RACES_COUNT, len(prev_races_sorted))):
                        prev_row = prev_races_sorted.iloc[i]
                        prefix = f"前走{i + 1}_"
                        # target_dfに存在するカラムのみを抽出（fallback禁止のため、存在チェック後にエラー）
                        if "着順" in prev_race_columns:
                            if "着順" not in prev_row.index: raise ValueError(f"前走データに'着順'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                            row_data[f"{prefix}着順"] = prev_row["着順"]
                        if "タイム" in prev_race_columns:
                            if "タイム" not in prev_row.index: raise ValueError(f"前走データに'タイム'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                            row_data[f"{prefix}タイム"] = prev_row["タイム"]
                        if "距離" in prev_race_columns:
                            if "距離" not in prev_row.index: raise ValueError(f"前走データに'距離'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                            row_data[f"{prefix}距離"] = prev_row["距離"]
                        if "頭数" in prev_race_columns:
                            if "頭数" not in prev_row.index: raise ValueError(f"前走データに'頭数'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                            row_data[f"{prefix}頭数"] = prev_row["頭数"]
                        if "芝ダ障害コード" in prev_race_columns:
                            if "芝ダ障害コード" not in prev_row.index: raise ValueError(f"前走データに'芝ダ障害コード'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                            row_data[f"{prefix}芝ダ障害コード"] = prev_row["芝ダ障害コード"]
                        if "馬場状態" in prev_race_columns:
                            if "馬場状態" not in prev_row.index: raise ValueError(f"前走データに'馬場状態'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                            row_data[f"{prefix}馬場状態"] = prev_row["馬場状態"]
                        # race_keyは必須（日程情報、リーク検証用）
                        if "race_key" not in prev_row.index: raise ValueError(f"前走データに'race_key'カラムが存在しません。利用可能なカラム: {list(prev_row.index)[:10]}")
                        row_data[f"前走{i + 1}レースキー_SED"] = prev_row["race_key"]
                        # 枠番、R、馬番も追加
                        if "枠番" in prev_row.index:
                            row_data[f"{prefix}枠番"] = prev_row["枠番"]
                        if "R" in prev_row.index:
                            row_data[f"{prefix}R"] = prev_row["R"]
                        if "馬番" in prev_row.index:
                            row_data[f"{prefix}馬番"] = prev_row["馬番"]
                    
                    # 結果に追加
                    for col in prev_cols:
                        result_data[col].append(row_data.get(col, np.nan if "race_key" not in col else None))
                    result_indices.append(original_idx)
                
                # DataFrameに変換して追加
                if len(result_indices) > 0:
                    horse_prev_data = pd.DataFrame(result_data, index=result_indices)
                    result_dfs.append(horse_prev_data)
            
            # 結果を結合してDataFrameに反映
            if result_dfs:
                prev_data_df = pd.concat(result_dfs)
                for col in prev_cols:
                    if col in prev_data_df.columns:
                        # カラムが存在しない場合は追加（race_keyは文字列型、それ以外は数値型）
                        if col not in target_df.columns:
                            if "race_key" in col:
                                target_df[col] = None
                            else:
                                target_df[col] = np.nan
                        # 値を設定（型の不一致を防ぐため、Noneを含む可能性がある場合は常にobject型に変換）
                        col_data = prev_data_df[col]
                        # result_dataにNoneが追加されている可能性があるため、target_dfのカラムもobject型に変換
                        if target_df[col].dtype != 'object' or col_data.dtype != 'object':
                            target_df[col] = target_df[col].astype(object)
                            target_df.loc[prev_data_df.index, col] = col_data.astype(object)
                        else:
                            target_df.loc[prev_data_df.index, col] = col_data
            
            # MultiIndexの場合はreset_indexしてカラムとして使用可能にする
            if isinstance(target_df.index, pd.MultiIndex) and target_df.index.names == PreviousRaceExtractor.MERGE_KEYS: target_df = target_df.reset_index()
            
            # スキーマ検証
            schema.validate(target_df)
            
            return target_df
        finally:
            # メモリクリーンアップ
            if 'all_races_df' in locals() and all_races_df is not None: del all_races_df
            gc.collect()
