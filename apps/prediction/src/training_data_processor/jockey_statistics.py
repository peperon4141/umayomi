"""騎手の過去成績統計を計算するクラス"""

import multiprocessing
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm


def _process_group_time_series_stats(
    group_value, group_stats, group_targets, group_col, time_col, prefix
):
    """グループごとの時系列統計量を計算（並列化用）"""
    group_stats = group_stats.sort_values(by=time_col).reset_index(drop=True)
    
    if len(group_stats) == 0 or len(group_targets) == 0:
        return pd.DataFrame()
    
    group_stats_times = group_stats[time_col].values
    group_targets_times = group_targets[time_col].values
    group_targets_indices = group_targets['_original_index'].values
    indices = np.searchsorted(group_stats_times, group_targets_times, side='left') - 1
    
    n_targets = len(group_targets)
    result_data = {
        group_col: [group_value] * n_targets,
        time_col: group_targets_times,
        '_original_index': group_targets_indices,
    }
    
    valid_mask = indices >= 0
    cumsum_1st_col = group_stats[f"{prefix}_cumsum_1st"].values
    cumsum_3rd_col = group_stats[f"{prefix}_cumsum_3rd"].values
    cumsum_rank_col = group_stats[f"{prefix}_cumsum_rank"].values
    cumcount_col = group_stats[f"{prefix}_cumcount"].values
    
    result_data[f"{prefix}_cumsum_1st"] = np.zeros(n_targets, dtype=float)
    result_data[f"{prefix}_cumsum_3rd"] = np.zeros(n_targets, dtype=float)
    result_data[f"{prefix}_cumsum_rank"] = np.zeros(n_targets, dtype=float)
    result_data[f"{prefix}_cumcount"] = np.zeros(n_targets, dtype=int)
    
    if valid_mask.any():
        valid_indices = indices[valid_mask]
        result_data[f"{prefix}_cumsum_1st"][valid_mask] = cumsum_1st_col[valid_indices]
        result_data[f"{prefix}_cumsum_3rd"][valid_mask] = cumsum_3rd_col[valid_indices]
        result_data[f"{prefix}_cumsum_rank"][valid_mask] = cumsum_rank_col[valid_indices]
        result_data[f"{prefix}_cumcount"][valid_mask] = cumcount_col[valid_indices]
    
    return pd.DataFrame(result_data)


def _process_group_recent_races(
    group_value, group_stats, group_targets, group_col, time_col, num_races, prefix
):
    """グループごとの直近レースを抽出（並列化用）"""
    group_stats = group_stats.sort_values(by=time_col).reset_index(drop=True)
    
    prefix_jp = {"horse": "馬", "jockey": "騎手", "trainer": "調教師"}.get(prefix)
    if not prefix_jp:
        raise ValueError(f"未知のprefix: {prefix}")
    
    field_mapping = {
        'rank': '着順', 'time': 'タイム', 'distance': '距離',
        'course_type': '芝ダ障害コード', 'ground_condition': '馬場状態',
        'num_horses': '頭数', 'race_num': 'R'
    }
    
    if len(group_stats) == 0 or len(group_targets) == 0:
        result_cols = [group_col, time_col, '_original_index'] + [
            f"{prefix_jp}直近{i}{field_mapping[col]}"
            for i in range(1, num_races + 1)
            for col in ['rank', 'time', 'distance', 'course_type', 'ground_condition', 'num_horses', 'race_num']
        ]
        return pd.DataFrame(columns=result_cols)
    
    group_stats_times = group_stats[time_col].values
    group_targets_times = group_targets[time_col].values
    group_targets_indices = group_targets['_original_index'].values
    n_targets = len(group_targets)
    
    result_data = {
        group_col: np.full(n_targets, group_value),
        time_col: group_targets_times,
        '_original_index': group_targets_indices,
    }
    
    for i in range(1, num_races + 1):
        for en_col, jp_col in field_mapping.items():
            result_data[f"{prefix_jp}直近{i}{jp_col}"] = np.full(n_targets, np.nan, dtype=float)
    
    stats_cols = ["着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
    available_cols = [col for col in stats_cols if col in group_stats.columns]
    stats_arrays = {col: group_stats[col].values for col in available_cols}
    
    search_indices = np.searchsorted(group_stats_times, group_targets_times, side='left')
    
    for target_idx in range(n_targets):
        past_count = search_indices[target_idx]
        if past_count > 0:
            start_idx = max(0, past_count - num_races)
            recent_indices = np.arange(start_idx, past_count)
            for i in range(1, num_races + 1):
                race_idx_in_recent = len(recent_indices) - i
                if race_idx_in_recent >= 0:
                    race_idx = recent_indices[race_idx_in_recent]
                    for en_col, jp_col in field_mapping.items():
                        if jp_col in stats_arrays:
                            result_data[f"{prefix_jp}直近{i}{jp_col}"][target_idx] = stats_arrays[jp_col][race_idx]
    
    return pd.DataFrame(result_data)


class JockeyStatistics:
    """騎手の過去成績統計を計算するクラス"""

    @staticmethod
    def calculate(stats_df: pd.DataFrame, target_df: pd.DataFrame) -> pd.DataFrame:
        """騎手の過去成績統計特徴量と直近3レース詳細を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
        if "騎手コード" not in target_df.columns:
            return target_df

        target_original_index = target_df.index.copy()
        target_df_sorted = target_df.sort_values(by=["騎手コード", "start_datetime"]).reset_index(drop=True)
        target_df_sorted['_original_index'] = target_original_index.values
        
        jockey_stats = JockeyStatistics._calculate_time_series_stats(
            stats_df, target_df_sorted, "騎手コード", "start_datetime", "jockey"
        )
        jockey_recent_races = JockeyStatistics._extract_recent_races(
            stats_df, target_df_sorted, "騎手コード", "start_datetime", num_races=3, prefix="jockey"
        )
        
        key_cols = ["騎手コード", "start_datetime"]
        assert len(target_df_sorted) == len(jockey_stats), "行数が一致しません"
        keys_match = (target_df_sorted[key_cols].values == jockey_stats[key_cols].values).all()
        
        if not keys_match:
            target_df_merged = target_df_sorted.merge(
                jockey_stats, on=key_cols, how="left", suffixes=("", "_jockey_stats"), sort=False
            )
        else:
            target_df_merged = target_df_sorted.copy()
            for col in jockey_stats.columns:
                if col not in key_cols:
                    target_df_merged[col] = jockey_stats[col].values
        
        assert len(target_df_merged) == len(jockey_recent_races), "行数が一致しません"
        keys_match_recent = (target_df_merged[key_cols].values == jockey_recent_races[key_cols].values).all()
        
        if not keys_match_recent:
            target_df_merged = target_df_merged.merge(
                jockey_recent_races, on=key_cols, how="left", suffixes=("", "_jockey_recent"), sort=False
            )
        else:
            for col in jockey_recent_races.columns:
                if col not in key_cols:
                    target_df_merged[col] = jockey_recent_races[col].values
        
        target_index_df = pd.DataFrame({'_original_index': target_original_index})
        target_df = target_index_df.merge(target_df_merged, on='_original_index', how='left').drop(columns=['_original_index'])
        target_df.index = target_original_index
        
        return target_df

    @staticmethod
    def _calculate_time_series_stats(
        stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, prefix: str
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータのみを使って統計量を計算（未来情報を完全に除外）。"""
        target_original_index = target_df['_original_index'].values if '_original_index' in target_df.columns else target_df.index.copy()
        target_sorted = target_df[[group_col, time_col]]
        target_sorted['_original_index'] = target_df.index.values
        
        stats_df_clean = stats_df.dropna(subset=[group_col, time_col])
        target_sorted = target_sorted.dropna(subset=[group_col, time_col])
        stats_sorted = stats_df_clean.sort_values(by=[group_col, time_col]).reset_index(drop=True)
        
        stats_sorted[f"{prefix}_cumsum_1st"] = stats_sorted.groupby(group_col)["rank_1st"].cumsum()
        stats_sorted[f"{prefix}_cumsum_3rd"] = stats_sorted.groupby(group_col)["rank_3rd"].cumsum()
        stats_sorted[f"{prefix}_cumsum_rank"] = stats_sorted.groupby(group_col)["着順"].cumsum()
        stats_sorted[f"{prefix}_cumcount"] = stats_sorted.groupby(group_col).cumcount() + 1
        
        grouped_stats = stats_sorted.groupby(group_col, sort=False)
        target_groups = set(target_sorted[group_col].unique())
        grouped_targets = target_sorted.groupby(group_col, sort=False)
        group_data_list = [
            (group_value, grouped_stats.get_group(group_value), grouped_targets.get_group(group_value)[[group_col, time_col, '_original_index']])
            for group_value in target_groups
            if group_value in grouped_stats.groups and group_value in grouped_targets.groups
        ]
        
        if len(group_data_list) == 0:
            return pd.DataFrame(columns=[group_col, time_col, '_original_index',
                                        f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd",
                                        f"{prefix}_cumsum_rank", f"{prefix}_cumcount"])
        
        n_jobs = max(1, multiprocessing.cpu_count() - 1)
        batch_size = max(50, min(500, len(group_data_list) // n_jobs))
        
        with tqdm(total=len(group_data_list), desc=f"{prefix}グループ処理", leave=True, unit="groups") as pbar:
            results = Parallel(n_jobs=n_jobs, batch_size=batch_size, verbose=0)(
                delayed(_process_group_time_series_stats)(
                    group_value, group_stats, group_targets, group_col, time_col, prefix
                ) for group_value, group_stats, group_targets in group_data_list
            )
            for result_df in results:
                if len(result_df) > 0:
                    pbar.update(1)
        
        merged = pd.concat([df for df in results if len(df) > 0], ignore_index=True) if results else pd.DataFrame(
            columns=[group_col, time_col, '_original_index',
                    f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd",
                    f"{prefix}_cumsum_rank", f"{prefix}_cumcount"]
        )
        
        prefix_jp = {"horse": "馬", "jockey": "騎手", "trainer": "調教師"}.get(prefix)
        if not prefix_jp:
            raise ValueError(f"未知のprefix: {prefix}")
        
        merged[f"{prefix_jp}勝率"] = (merged[f"{prefix}_cumsum_1st"] / merged[f"{prefix}_cumcount"]).fillna(0.0)
        merged[f"{prefix_jp}連対率"] = (merged[f"{prefix}_cumsum_3rd"] / merged[f"{prefix}_cumcount"]).fillna(0.0)
        merged[f"{prefix_jp}平均着順"] = (merged[f"{prefix}_cumsum_rank"] / merged[f"{prefix}_cumcount"]).fillna(0.0)
        merged[f"{prefix_jp}出走回数"] = merged[f"{prefix}_cumcount"].fillna(0).astype(int)
        
        target_index_df = pd.DataFrame({'_original_index': target_original_index})
        result = target_index_df.merge(merged, on='_original_index', how='left').drop(columns=['_original_index'])
        result.index = target_original_index
        
        return result[[group_col, time_col, f"{prefix_jp}勝率", f"{prefix_jp}連対率", f"{prefix_jp}平均着順", f"{prefix_jp}出走回数"]]

    @staticmethod
    def _extract_recent_races(
        stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, num_races: int = 3, prefix: str = "jockey"
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータから直近Nレースの詳細情報を抽出（未来情報を完全に除外）。"""
        target_original_index = target_df.index.copy()
        stats_cols = ["着順", "タイム", "距離", "芝ダ障害コード", "馬場状態", "頭数", "R"]
        available_cols = [col for col in stats_cols if col in stats_df.columns]
        stats_df_subset = stats_df[[group_col, time_col] + available_cols]
        target_df_subset = target_df[[group_col, time_col]]
        target_df_subset['_original_index'] = target_df.index.values
        
        grouped_stats = stats_df_subset.groupby(group_col, sort=False)
        target_groups = set(target_df_subset[group_col].unique())
        grouped_targets = target_df_subset.groupby(group_col, sort=False)
        group_data_list = [
            (group_value, grouped_stats.get_group(group_value), grouped_targets.get_group(group_value)[[group_col, time_col, '_original_index']])
            for group_value in target_groups
            if group_value in grouped_stats.groups and group_value in grouped_targets.groups
        ]
        
        if len(group_data_list) == 0:
            prefix_jp = {"horse": "馬", "jockey": "騎手", "trainer": "調教師"}.get(prefix)
            if not prefix_jp:
                raise ValueError(f"未知のprefix: {prefix}")
            field_mapping = {
                'rank': '着順', 'time': 'タイム', 'distance': '距離',
                'course_type': '芝ダ障害コード', 'ground_condition': '馬場状態',
                'num_horses': '頭数', 'race_num': 'R'
            }
            result_cols = [group_col, time_col, '_original_index'] + [
                f"{prefix_jp}直近{i}{field_mapping[col]}"
                for i in range(1, num_races + 1)
                for col in ['rank', 'time', 'distance', 'course_type', 'ground_condition', 'num_horses', 'race_num']
            ]
            return pd.DataFrame(index=target_original_index, columns=result_cols)
        
        n_jobs = max(1, multiprocessing.cpu_count() - 1)
        batch_size = max(50, min(500, len(group_data_list) // n_jobs))
        
        with tqdm(total=len(group_data_list), desc=f"{prefix}直近レース抽出", leave=True, unit="groups") as pbar:
            results = Parallel(n_jobs=n_jobs, batch_size=batch_size, verbose=0)(
                delayed(_process_group_recent_races)(
                    group_value, group_stats, group_targets, group_col, time_col, num_races, prefix
                ) for group_value, group_stats, group_targets in group_data_list
            )
            for result_df in results:
                if len(result_df) > 0:
                    pbar.update(1)
        
        result_df = pd.concat([df for df in results if len(df) > 0], ignore_index=True) if results else pd.DataFrame()
        
        if len(result_df) > 0 and '_original_index' in result_df.columns:
            target_index_df = pd.DataFrame({'_original_index': target_original_index})
            result_df = target_index_df.merge(result_df, on='_original_index', how='left').drop(columns=['_original_index'])
            result_df.index = target_original_index
        else:
            prefix_jp = {"horse": "馬", "jockey": "騎手", "trainer": "調教師"}.get(prefix)
            if not prefix_jp:
                raise ValueError(f"未知のprefix: {prefix}")
            field_mapping = {
                'rank': '着順', 'time': 'タイム', 'distance': '距離',
                'course_type': '芝ダ障害コード', 'ground_condition': '馬場状態',
                'num_horses': '頭数', 'race_num': 'R'
            }
            result_cols = [group_col, time_col] + [
                f"{prefix_jp}直近{i}{field_mapping[col]}"
                for i in range(1, num_races + 1)
                for col in ['rank', 'time', 'distance', 'course_type', 'ground_condition', 'num_horses', 'race_num']
            ]
            result_df = pd.DataFrame(index=target_original_index, columns=result_cols)
        
        return result_df
