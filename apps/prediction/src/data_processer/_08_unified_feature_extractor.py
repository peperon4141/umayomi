"""統合的な特徴量抽出処理（前走データと統計特徴量を1回のgroupbyで計算）"""

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.utils.feature_converter import FeatureConverter


class UnifiedFeatureExtractor:
    """統合的な特徴量抽出クラス（staticメソッドのみ）"""

    @staticmethod
    def extract_all_features(
        df: pd.DataFrame, 
        sed_df: pd.DataFrame, 
        bac_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        前走データと統計特徴量を統合的に抽出（1回のgroupbyと時系列フィルタリングで全て計算）
        
        Args:
            df: 結合済みDataFrame（日本語キー）
            sed_df: SEDデータ
            bac_df: BACデータ（必須）
        
        Returns:
            全特徴量が追加されたDataFrame（日本語キー）
        """
        if sed_df is None:
            return df
        if bac_df is None:
            raise ValueError("BACデータは必須です。bac_dfがNoneです。")
        
        # 前処理：共通データ準備
        # add_start_datetime_to_df内でcopy()が実行されるため、ここでのcopy()は不要
        df_with_datetime = FeatureConverter.add_start_datetime_to_df(df)
        sed_df_with_key = FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
        
        # stats_dfを準備（統計量計算用）
        stats_cols = ["race_key", "馬番", "血統登録番号", "騎手コード", "調教師コード", "着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
        # 枠番が存在する場合は追加
        if "枠番" in sed_df_with_key.columns:
            stats_cols.append("枠番")
        # 列の抽出は新しいDataFrameを作成するため、明示的なcopy()は不要
        stats_df = sed_df_with_key[stats_cols]
        stats_df = stats_df.copy()  # 統計量計算で変更するため、ここでcopy()が必要
        stats_df["rank_1st"] = (stats_df["着順"] == 1).astype(int)
        stats_df["rank_3rd"] = (stats_df["着順"].isin([1, 2, 3])).astype(int)
        stats_df["start_datetime"] = FeatureConverter.get_datetime_from_race_key_vectorized(stats_df["race_key"])
        
        # 結果を格納するDataFrame（df_with_datetimeをベースに）
        # 前走データを追加するため、コピーが必要
        result_df = df_with_datetime.copy()
        original_index = result_df.index
        
        # 前走データ用のカラムを初期化
        for i in range(1, 6):
            prev_cols = [
                f"prev_{i}_race_num",  # R
                f"prev_{i}_num_horses",  # 頭数
                f"prev_{i}_frame",  # 枠番
                f"prev_{i}_horse_number",  # 馬番
                f"prev_{i}_rank",  # 着順
                f"prev_{i}_time",  # タイム
                f"prev_{i}_distance",  # 距離
                f"prev_{i}_course_type",  # 芝ダ障害コード
                f"prev_{i}_ground_condition",  # 馬場状態
                f"prev_{i}_race_key",  # レースキー（リーク検証用）
            ]
            for col in prev_cols:
                if col not in result_df.columns:
                    if "race_key" in col:
                        result_df[col] = None
                    else:
                        result_df[col] = np.nan
        
        # 統計量用のカラムを初期化
        stat_cols = [
            "馬勝率", "馬連対率", "馬平均着順", "馬出走回数",
            "騎手勝率", "騎手連対率", "騎手平均着順", "騎手出走回数",
            "調教師勝率", "調教師連対率", "調教師平均着順", "調教師出走回数",
        ]
        for col in stat_cols:
            if col not in result_df.columns:
                result_df[col] = np.nan
        
        # 直近レース用のカラムを初期化
        for prefix_jp in ["騎手", "調教師"]:
            for i in range(1, 4):
                for field in ["着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]:
                    col = f"{prefix_jp}直近{i}{field}"
                    if col not in result_df.columns:
                        result_df[col] = np.nan
                col = f"{prefix_jp}直近{i}race_key"
                if col not in result_df.columns:
                    result_df[col] = None
        
        # 馬ごとにgroupbyして、1回の時系列フィルタリングで全ての特徴量を計算
        if "血統登録番号" in result_df.columns and "血統登録番号" in stats_df.columns:
            print("馬ごとの特徴量抽出中...")
            result_df = UnifiedFeatureExtractor._extract_horse_features(result_df, stats_df)
        
        # 騎手ごとにgroupbyして、1回の時系列フィルタリングで全ての特徴量を計算
        if "騎手コード" in result_df.columns and "騎手コード" in stats_df.columns:
            print("騎手ごとの特徴量抽出中...")
            result_df = UnifiedFeatureExtractor._extract_jockey_features(result_df, stats_df)
        
        # 調教師ごとにgroupbyして、1回の時系列フィルタリングで全ての特徴量を計算
        if "調教師コード" in result_df.columns and "調教師コード" in stats_df.columns:
            print("調教師ごとの特徴量抽出中...")
            result_df = UnifiedFeatureExtractor._extract_trainer_features(result_df, stats_df)
        
        result_df.index = original_index
        return result_df

    @staticmethod
    def _extract_horse_features(target_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
        """
        馬ごとの特徴量を統合的に抽出（前走データ + 統計量を1回のgroupbyで計算）
        """
        # 馬ごとにgroupby
        target_sorted = target_df.sort_values(by=["血統登録番号", "start_datetime"]).reset_index(drop=True)
        target_sorted['_original_index'] = target_df.index.values
        
        stats_sorted = stats_df.sort_values(by=["血統登録番号", "start_datetime"]).reset_index(drop=True)
        
        # 累積統計量を事前計算
        stats_sorted["horse_cumsum_1st"] = stats_sorted.groupby("血統登録番号")["rank_1st"].cumsum()
        stats_sorted["horse_cumsum_3rd"] = stats_sorted.groupby("血統登録番号")["rank_3rd"].cumsum()
        stats_sorted["horse_cumsum_rank"] = stats_sorted.groupby("血統登録番号")["着順"].cumsum()
        stats_sorted["horse_cumcount"] = stats_sorted.groupby("血統登録番号").cumcount() + 1
        
        grouped_stats = stats_sorted.groupby("血統登録番号", sort=False)
        grouped_targets = target_sorted.groupby("血統登録番号", sort=False)
        
        valid_groups = [g for g in grouped_targets.groups.keys() if g in grouped_stats.groups]
        
        results = []
        with tqdm(total=len(valid_groups), desc="馬特徴量抽出", leave=True, unit="頭") as pbar:
            for horse_id in valid_groups:
                group_stats = grouped_stats.get_group(horse_id)
                group_targets = grouped_targets.get_group(horse_id)
                
                result_df = UnifiedFeatureExtractor._process_horse_group(horse_id, group_stats, group_targets)
                if len(result_df) > 0:
                    results.append(result_df)
                pbar.update(1)
        
        if not results:
            return target_df
        
        merged = pd.concat(results, ignore_index=True)
        target_index_df = pd.DataFrame({'_original_index': target_df.index.values})
        result = target_index_df.merge(merged, on='_original_index', how='left').drop(columns=['_original_index'])
        result.index = target_df.index
        
        # 結果をtarget_dfに反映
        for col in merged.columns:
            if col not in ['血統登録番号', 'start_datetime', '_original_index']:
                target_df[col] = result[col].values
        
        return target_df

    @staticmethod
    def _process_horse_group(
        horse_id, group_stats: pd.DataFrame, group_targets: pd.DataFrame
    ) -> pd.DataFrame:
        """
        1頭の馬のグループに対して、前走データと統計量を同時に計算
        """
        group_stats = group_stats.sort_values(by="start_datetime").reset_index(drop=True)
        group_targets = group_targets.sort_values(by="start_datetime").reset_index(drop=True)
        
        if len(group_stats) == 0 or len(group_targets) == 0:
            return pd.DataFrame()
        
        group_stats_times = group_stats["start_datetime"].values
        group_targets_times = group_targets["start_datetime"].values
        group_targets_indices = group_targets['_original_index'].values
        n_targets = len(group_targets)
        
        # 結果データの初期化
        result_data = {
            '血統登録番号': [horse_id] * n_targets,
            'start_datetime': group_targets_times,
            '_original_index': group_targets_indices,
        }
        
        # 前走データ用のカラムを初期化
        for i in range(1, 6):
            for field in ['race_num', 'num_horses', 'frame', 'horse_number', 'rank', 'time', 'distance', 'course_type', 'ground_condition', 'race_key']:
                result_data[f"prev_{i}_{field}"] = [np.nan] * n_targets if field != 'race_key' else [None] * n_targets
        
        # 統計量用のカラムを初期化
        result_data['馬勝率'] = np.zeros(n_targets, dtype=float)
        result_data['馬連対率'] = np.zeros(n_targets, dtype=float)
        result_data['馬平均着順'] = np.zeros(n_targets, dtype=float)
        result_data['馬出走回数'] = np.zeros(n_targets, dtype=int)
        
        # 各ターゲットレースに対して処理
        for target_idx, target_time in enumerate(group_targets_times):
            # 時系列フィルタリング：現在のレースより前のレースを取得
            past_mask = group_stats_times < target_time
            past_indices = np.where(past_mask)[0]
            
            if len(past_indices) == 0:
                continue
            
            # 前走データ（過去5走）
            prev_indices = past_indices[-5:] if len(past_indices) >= 5 else past_indices
            prev_races = group_stats.iloc[prev_indices[::-1]]  # 新しい順にソート
            
            for i, (prev_idx, prev_row) in enumerate(zip(prev_indices[::-1], prev_races.itertuples()), 1):
                if i > 5:
                    break
                result_data[f"prev_{i}_race_num"][target_idx] = prev_row.R
                result_data[f"prev_{i}_num_horses"][target_idx] = prev_row.頭数
                result_data[f"prev_{i}_frame"][target_idx] = getattr(prev_row, "枠番", np.nan) if hasattr(prev_row, "枠番") else np.nan
                result_data[f"prev_{i}_horse_number"][target_idx] = prev_row.馬番
                result_data[f"prev_{i}_rank"][target_idx] = prev_row.着順
                result_data[f"prev_{i}_time"][target_idx] = prev_row.タイム
                result_data[f"prev_{i}_distance"][target_idx] = prev_row.距離
                result_data[f"prev_{i}_course_type"][target_idx] = prev_row.芝ダ障害コード
                result_data[f"prev_{i}_ground_condition"][target_idx] = prev_row.馬場状態
                result_data[f"prev_{i}_race_key"][target_idx] = prev_row.race_key
            
            # 統計量（累積値から取得）
            last_past_idx = past_indices[-1]
            result_data['馬出走回数'][target_idx] = group_stats.iloc[last_past_idx]["horse_cumcount"]
            cumsum_1st = group_stats.iloc[last_past_idx]["horse_cumsum_1st"]
            cumsum_3rd = group_stats.iloc[last_past_idx]["horse_cumsum_3rd"]
            cumsum_rank = group_stats.iloc[last_past_idx]["horse_cumsum_rank"]
            cumcount = group_stats.iloc[last_past_idx]["horse_cumcount"]
            
            if cumcount > 0:
                result_data['馬勝率'][target_idx] = cumsum_1st / cumcount
                result_data['馬連対率'][target_idx] = cumsum_3rd / cumcount
                result_data['馬平均着順'][target_idx] = cumsum_rank / cumcount
        
        return pd.DataFrame(result_data)

    @staticmethod
    def _extract_jockey_features(target_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
        """
        騎手ごとの特徴量を統合的に抽出（統計量 + 直近3レースを1回のgroupbyで計算）
        """
        target_sorted = target_df.sort_values(by=["騎手コード", "start_datetime"]).reset_index(drop=True)
        target_sorted['_original_index'] = target_df.index.values
        
        stats_sorted = stats_df.sort_values(by=["騎手コード", "start_datetime"]).reset_index(drop=True)
        
        # 累積統計量を事前計算
        stats_sorted["jockey_cumsum_1st"] = stats_sorted.groupby("騎手コード")["rank_1st"].cumsum()
        stats_sorted["jockey_cumsum_3rd"] = stats_sorted.groupby("騎手コード")["rank_3rd"].cumsum()
        stats_sorted["jockey_cumsum_rank"] = stats_sorted.groupby("騎手コード")["着順"].cumsum()
        stats_sorted["jockey_cumcount"] = stats_sorted.groupby("騎手コード").cumcount() + 1
        
        grouped_stats = stats_sorted.groupby("騎手コード", sort=False)
        grouped_targets = target_sorted.groupby("騎手コード", sort=False)
        
        valid_groups = [g for g in grouped_targets.groups.keys() if g in grouped_stats.groups]
        
        results = []
        with tqdm(total=len(valid_groups), desc="騎手特徴量抽出", leave=True, unit="人") as pbar:
            for jockey_id in valid_groups:
                group_stats = grouped_stats.get_group(jockey_id)
                group_targets = grouped_targets.get_group(jockey_id)
                
                result_df = UnifiedFeatureExtractor._process_jockey_group(jockey_id, group_stats, group_targets)
                if len(result_df) > 0:
                    results.append(result_df)
                pbar.update(1)
        
        if not results:
            return target_df
        
        merged = pd.concat(results, ignore_index=True)
        target_index_df = pd.DataFrame({'_original_index': target_df.index.values})
        result = target_index_df.merge(merged, on='_original_index', how='left').drop(columns=['_original_index'])
        result.index = target_df.index
        
        # 結果をtarget_dfに反映
        for col in merged.columns:
            if col not in ['騎手コード', 'start_datetime', '_original_index']:
                target_df[col] = result[col].values
        
        return target_df

    @staticmethod
    def _process_jockey_group(
        jockey_id, group_stats: pd.DataFrame, group_targets: pd.DataFrame
    ) -> pd.DataFrame:
        """
        1人の騎手のグループに対して、統計量と直近3レースを同時に計算
        """
        group_stats = group_stats.sort_values(by="start_datetime").reset_index(drop=True)
        group_targets = group_targets.sort_values(by="start_datetime").reset_index(drop=True)
        
        if len(group_stats) == 0 or len(group_targets) == 0:
            return pd.DataFrame()
        
        group_stats_times = group_stats["start_datetime"].values
        group_targets_times = group_targets["start_datetime"].values
        group_targets_indices = group_targets['_original_index'].values
        n_targets = len(group_targets)
        
        # 結果データの初期化
        result_data = {
            '騎手コード': [jockey_id] * n_targets,
            'start_datetime': group_targets_times,
            '_original_index': group_targets_indices,
        }
        
        # 統計量用のカラムを初期化
        result_data['騎手勝率'] = np.zeros(n_targets, dtype=float)
        result_data['騎手連対率'] = np.zeros(n_targets, dtype=float)
        result_data['騎手平均着順'] = np.zeros(n_targets, dtype=float)
        result_data['騎手出走回数'] = np.zeros(n_targets, dtype=int)
        
        # 直近レース用のカラムを初期化
        field_mapping = {
            'rank': '着順', 'time': 'タイム', 'distance': '距離',
            'course_type': '芝ダ障害コード', 'ground_condition': '馬場状態',
            'num_horses': '頭数', 'race_num': 'R'
        }
        for i in range(1, 4):
            for en_col, jp_col in field_mapping.items():
                result_data[f"騎手直近{i}{jp_col}"] = np.full(n_targets, np.nan, dtype=float)
            result_data[f"騎手直近{i}race_key"] = [None] * n_targets
        
        # 各ターゲットレースに対して処理
        for target_idx, target_time in enumerate(group_targets_times):
            # 時系列フィルタリング：現在のレースより前のレースを取得
            past_mask = group_stats_times < target_time
            past_indices = np.where(past_mask)[0]
            
            if len(past_indices) == 0:
                continue
            
            # 統計量（累積値から取得）
            last_past_idx = past_indices[-1]
            result_data['騎手出走回数'][target_idx] = group_stats.iloc[last_past_idx]["jockey_cumcount"]
            cumsum_1st = group_stats.iloc[last_past_idx]["jockey_cumsum_1st"]
            cumsum_3rd = group_stats.iloc[last_past_idx]["jockey_cumsum_3rd"]
            cumsum_rank = group_stats.iloc[last_past_idx]["jockey_cumsum_rank"]
            cumcount = group_stats.iloc[last_past_idx]["jockey_cumcount"]
            
            if cumcount > 0:
                result_data['騎手勝率'][target_idx] = cumsum_1st / cumcount
                result_data['騎手連対率'][target_idx] = cumsum_3rd / cumcount
                result_data['騎手平均着順'][target_idx] = cumsum_rank / cumcount
            
            # 直近3レース
            recent_indices = past_indices[-3:] if len(past_indices) >= 3 else past_indices
            recent_races = group_stats.iloc[recent_indices[::-1]]  # 新しい順にソート
            
            for i, (race_idx, race_row) in enumerate(zip(recent_indices[::-1], recent_races.itertuples()), 1):
                if i > 3:
                    break
                for en_col, jp_col in field_mapping.items():
                    if hasattr(race_row, jp_col):
                        result_data[f"騎手直近{i}{jp_col}"][target_idx] = getattr(race_row, jp_col)
                result_data[f"騎手直近{i}race_key"][target_idx] = race_row.race_key
        
        return pd.DataFrame(result_data)

    @staticmethod
    def _extract_trainer_features(target_df: pd.DataFrame, stats_df: pd.DataFrame) -> pd.DataFrame:
        """
        調教師ごとの特徴量を統合的に抽出（統計量 + 直近3レースを1回のgroupbyで計算）
        """
        target_sorted = target_df.sort_values(by=["調教師コード", "start_datetime"]).reset_index(drop=True)
        target_sorted['_original_index'] = target_df.index.values
        
        stats_sorted = stats_df.sort_values(by=["調教師コード", "start_datetime"]).reset_index(drop=True)
        
        # 累積統計量を事前計算
        stats_sorted["trainer_cumsum_1st"] = stats_sorted.groupby("調教師コード")["rank_1st"].cumsum()
        stats_sorted["trainer_cumsum_3rd"] = stats_sorted.groupby("調教師コード")["rank_3rd"].cumsum()
        stats_sorted["trainer_cumsum_rank"] = stats_sorted.groupby("調教師コード")["着順"].cumsum()
        stats_sorted["trainer_cumcount"] = stats_sorted.groupby("調教師コード").cumcount() + 1
        
        grouped_stats = stats_sorted.groupby("調教師コード", sort=False)
        grouped_targets = target_sorted.groupby("調教師コード", sort=False)
        
        valid_groups = [g for g in grouped_targets.groups.keys() if g in grouped_stats.groups]
        
        results = []
        with tqdm(total=len(valid_groups), desc="調教師特徴量抽出", leave=True, unit="人") as pbar:
            for trainer_id in valid_groups:
                group_stats = grouped_stats.get_group(trainer_id)
                group_targets = grouped_targets.get_group(trainer_id)
                
                result_df = UnifiedFeatureExtractor._process_trainer_group(trainer_id, group_stats, group_targets)
                if len(result_df) > 0:
                    results.append(result_df)
                pbar.update(1)
        
        if not results:
            return target_df
        
        merged = pd.concat(results, ignore_index=True)
        target_index_df = pd.DataFrame({'_original_index': target_df.index.values})
        result = target_index_df.merge(merged, on='_original_index', how='left').drop(columns=['_original_index'])
        result.index = target_df.index
        
        # 結果をtarget_dfに反映
        for col in merged.columns:
            if col not in ['調教師コード', 'start_datetime', '_original_index']:
                target_df[col] = result[col].values
        
        return target_df

    @staticmethod
    def _process_trainer_group(
        trainer_id, group_stats: pd.DataFrame, group_targets: pd.DataFrame
    ) -> pd.DataFrame:
        """
        1人の調教師のグループに対して、統計量と直近3レースを同時に計算
        """
        group_stats = group_stats.sort_values(by="start_datetime").reset_index(drop=True)
        group_targets = group_targets.sort_values(by="start_datetime").reset_index(drop=True)
        
        if len(group_stats) == 0 or len(group_targets) == 0:
            return pd.DataFrame()
        
        group_stats_times = group_stats["start_datetime"].values
        group_targets_times = group_targets["start_datetime"].values
        group_targets_indices = group_targets['_original_index'].values
        n_targets = len(group_targets)
        
        # 結果データの初期化
        result_data = {
            '調教師コード': [trainer_id] * n_targets,
            'start_datetime': group_targets_times,
            '_original_index': group_targets_indices,
        }
        
        # 統計量用のカラムを初期化
        result_data['調教師勝率'] = np.zeros(n_targets, dtype=float)
        result_data['調教師連対率'] = np.zeros(n_targets, dtype=float)
        result_data['調教師平均着順'] = np.zeros(n_targets, dtype=float)
        result_data['調教師出走回数'] = np.zeros(n_targets, dtype=int)
        
        # 直近レース用のカラムを初期化
        field_mapping = {
            'rank': '着順', 'time': 'タイム', 'distance': '距離',
            'course_type': '芝ダ障害コード', 'ground_condition': '馬場状態',
            'num_horses': '頭数', 'race_num': 'R'
        }
        for i in range(1, 4):
            for en_col, jp_col in field_mapping.items():
                result_data[f"調教師直近{i}{jp_col}"] = np.full(n_targets, np.nan, dtype=float)
            result_data[f"調教師直近{i}race_key"] = [None] * n_targets
        
        # 各ターゲットレースに対して処理
        for target_idx, target_time in enumerate(group_targets_times):
            # 時系列フィルタリング：現在のレースより前のレースを取得
            past_mask = group_stats_times < target_time
            past_indices = np.where(past_mask)[0]
            
            if len(past_indices) == 0:
                continue
            
            # 統計量（累積値から取得）
            last_past_idx = past_indices[-1]
            result_data['調教師出走回数'][target_idx] = group_stats.iloc[last_past_idx]["trainer_cumcount"]
            cumsum_1st = group_stats.iloc[last_past_idx]["trainer_cumsum_1st"]
            cumsum_3rd = group_stats.iloc[last_past_idx]["trainer_cumsum_3rd"]
            cumsum_rank = group_stats.iloc[last_past_idx]["trainer_cumsum_rank"]
            cumcount = group_stats.iloc[last_past_idx]["trainer_cumcount"]
            
            if cumcount > 0:
                result_data['調教師勝率'][target_idx] = cumsum_1st / cumcount
                result_data['調教師連対率'][target_idx] = cumsum_3rd / cumcount
                result_data['調教師平均着順'][target_idx] = cumsum_rank / cumcount
            
            # 直近3レース
            recent_indices = past_indices[-3:] if len(past_indices) >= 3 else past_indices
            recent_races = group_stats.iloc[recent_indices[::-1]]  # 新しい順にソート
            
            for i, (race_idx, race_row) in enumerate(zip(recent_indices[::-1], recent_races.itertuples()), 1):
                if i > 3:
                    break
                for en_col, jp_col in field_mapping.items():
                    if hasattr(race_row, jp_col):
                        result_data[f"調教師直近{i}{jp_col}"][target_idx] = getattr(race_row, jp_col)
                result_data[f"調教師直近{i}race_key"][target_idx] = race_row.race_key
        
        return pd.DataFrame(result_data)
