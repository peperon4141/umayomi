"""馬の過去成績統計を計算するクラス"""

import numpy as np
import pandas as pd
from tqdm import tqdm


def _process_group_time_series_stats(
    group_value, group_stats, target_sorted, group_col, time_col, prefix
):
    """グループごとの時系列統計量を計算（並列化用）"""
    group_stats = group_stats.sort_values(by=time_col).reset_index(drop=True)
    group_targets = target_sorted[target_sorted[group_col] == group_value]
    
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


class HorseStatistics:
    """馬の過去成績統計を計算するクラス"""

    @staticmethod
    def calculate(stats_df: pd.DataFrame, target_df: pd.DataFrame) -> pd.DataFrame:
        """馬の過去成績統計特徴量を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
        if "血統登録番号" not in target_df.columns:
            return target_df

        target_original_index = target_df.index.copy()
        target_df_sorted = target_df.sort_values(by=["血統登録番号", "start_datetime"]).reset_index(drop=True)
        target_df_sorted['_original_index'] = target_original_index.values

        horse_stats = HorseStatistics._calculate_time_series_stats(
            stats_df, target_df_sorted, "血統登録番号", "start_datetime", "horse"
        )

        key_cols = ["血統登録番号", "start_datetime"]
        assert len(target_df_sorted) == len(horse_stats), "行数が一致しません"
        keys_match = (target_df_sorted[key_cols].values == horse_stats[key_cols].values).all()
        
        if not keys_match:
            target_df_merged = target_df_sorted.merge(
                horse_stats, on=key_cols, how="left", suffixes=("", "_horse_stats"), sort=False
            )
        else:
            # フラグメント化を回避するため、pd.concatを使用
            horse_stats_subset = horse_stats[[col for col in horse_stats.columns if col not in key_cols]].copy()
            target_df_merged = pd.concat([target_df_sorted, horse_stats_subset], axis=1)

        target_index_df = pd.DataFrame({'_original_index': target_original_index})
        target_df = target_index_df.merge(target_df_merged, on='_original_index', how='left').drop(columns=['_original_index'])
        target_df.index = target_original_index

        # 使用済みのDataFrameを削除
        del target_df_sorted, horse_stats, target_df_merged, target_index_df

        return target_df

    @staticmethod
    def _calculate_time_series_stats(
        stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, prefix: str
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータのみを使って統計量を計算（未来情報を完全に除外）。"""
        target_original_index = target_df['_original_index'].values if '_original_index' in target_df.columns else target_df.index.copy()
        stats_sorted = stats_df.sort_values(by=[group_col, time_col]).reset_index(drop=True)
        # 新しいDataFrameを直接作成（コピーを避ける）
        target_sorted = pd.DataFrame({
            group_col: target_df[group_col].values,
            time_col: target_df[time_col].values,
            '_original_index': target_df['_original_index'].values if '_original_index' in target_df.columns else target_df.index.values
        })
        
        stats_sorted[f"{prefix}_cumsum_1st"] = stats_sorted.groupby(group_col)["rank_1st"].cumsum()
        stats_sorted[f"{prefix}_cumsum_3rd"] = stats_sorted.groupby(group_col)["rank_3rd"].cumsum()
        stats_sorted[f"{prefix}_cumsum_rank"] = stats_sorted.groupby(group_col)["着順"].cumsum()
        stats_sorted[f"{prefix}_cumcount"] = stats_sorted.groupby(group_col).cumcount() + 1
        
        target_sorted = target_sorted.dropna(subset=[group_col, time_col])
        stats_sorted = stats_sorted.dropna(subset=[group_col, time_col])
        
        grouped_stats = stats_sorted.groupby(group_col, sort=False)
        target_groups = set(target_sorted[group_col].unique())
        valid_groups = [g for g in target_groups if g in grouped_stats.groups]
        
        if len(valid_groups) == 0:
            return pd.DataFrame(columns=[group_col, time_col, '_original_index',
                                        f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd",
                                        f"{prefix}_cumsum_rank", f"{prefix}_cumcount"])
        
        # シーケンシャル処理でメモリ使用量を削減
        results = []
        with tqdm(total=len(valid_groups), desc=f"{prefix}グループ処理", leave=True, unit="groups") as pbar:
            for group_value in valid_groups:
                group_stats = grouped_stats.get_group(group_value)
                result_df = _process_group_time_series_stats(
                    group_value, group_stats, target_sorted, group_col, time_col, prefix
                )
                if len(result_df) > 0:
                    results.append(result_df)
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
        
        # 使用済みのDataFrameを削除
        del target_sorted, stats_sorted, grouped_stats, merged, target_index_df
        
        return result[[group_col, time_col, f"{prefix_jp}勝率", f"{prefix_jp}連対率", f"{prefix_jp}平均着順", f"{prefix_jp}出走回数"]]
