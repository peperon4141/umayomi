"""騎手の過去成績統計を計算するクラス"""

import gc
import logging

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.utils.schema_loader import Schema

logger = logging.getLogger(__name__)


class JockeyStatistics:
    """騎手の過去成績統計を計算するクラス"""
    
    # 結合キー
    MERGE_KEYS = ["race_key", "馬番"]
    
    # グループ化カラム
    GROUP_COLUMN = "騎手コード"
    TIME_COLUMN = "start_datetime"
    
    # 統計量プレフィックス
    PREFIX = "jockey"
    JP_PREFIX = "騎手"
    
    # 直近レース抽出に使用するカラム（SEDデータに含まれるカラム）
    # スキーマファイル（jockey_statistics_schema.json）のoutputColumnsに定義されているカラム名と一致
    _REQUIRED_RECENT_RACE_COLUMNS = ["着順", "タイム", "馬場状態", "R", "芝ダ障害コード", "頭数", "距離"]
    
    # 直近レース数
    RECENT_RACES_COUNT = 3
    
    # プレフィックスマッピング（enum化も検討可能だが、現状のdictで十分）
    _PREFIX_JP_MAP = {"horse": "馬", "jockey": "騎手", "trainer": "調教師"}

    @staticmethod
    def calculate(stats_df: pd.DataFrame, target_df: pd.DataFrame, schema: Schema) -> pd.DataFrame:
        """騎手の過去成績統計特徴量と直近3レース詳細を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
        if len(stats_df) == 0: raise ValueError("stats_dfが空です。統計量計算に必要なデータが提供されていません。")
        if len(target_df) == 0: raise ValueError("target_dfが空です。特徴量追加先のデータが提供されていません。")
        
        merge_keys = JockeyStatistics.MERGE_KEYS

        try:
            target_df_sorted = target_df.sort_values(by=[JockeyStatistics.GROUP_COLUMN, JockeyStatistics.TIME_COLUMN])
            jockey_stats = JockeyStatistics._calculate_time_series_stats(stats_df, target_df_sorted, JockeyStatistics.GROUP_COLUMN, JockeyStatistics.TIME_COLUMN, JockeyStatistics.PREFIX)
            jockey_recent_races = JockeyStatistics._extract_recent_races(stats_df, target_df_sorted, JockeyStatistics.GROUP_COLUMN, JockeyStatistics.TIME_COLUMN, JockeyStatistics.RECENT_RACES_COUNT, JockeyStatistics.PREFIX)

            target_df_merged = target_df_sorted.reset_index()
            key_cols = [JockeyStatistics.GROUP_COLUMN, JockeyStatistics.TIME_COLUMN]
            
            jockey_stats_subset = JockeyStatistics._prepare_merge_subset(jockey_stats, key_cols, merge_keys, "jockey_stats")
            target_df_merged = target_df_merged.merge(jockey_stats_subset, on=merge_keys, how="left", suffixes=("", "_jockey_stats"))
            del jockey_stats, jockey_stats_subset
            gc.collect()
            
            jockey_recent_subset = JockeyStatistics._prepare_merge_subset(jockey_recent_races, key_cols, merge_keys, "jockey_recent_races")
            target_df_merged = target_df_merged.merge(jockey_recent_subset, on=merge_keys, how="left", suffixes=("", "_jockey_recent"))
            del target_df_sorted, jockey_recent_races, jockey_recent_subset
            gc.collect()

            result_df = target_df_merged.reset_index()
            
            # スキーマ検証
            schema.validate(result_df)
            
            return result_df
            
        except Exception as e:
            logger.error(f"騎手統計量計算エラー: {type(e).__name__}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _prepare_merge_subset(df: pd.DataFrame, key_cols: list[str], merge_keys: list[str], df_name: str) -> pd.DataFrame:
        """マージ用のサブセットを準備（インデックス処理を含む）"""
        subset = df[[col for col in df.columns if col not in key_cols]]
        if not all(col in subset.columns for col in merge_keys):
            if not isinstance(subset.index, pd.MultiIndex): raise ValueError(f"{df_name}に{merge_keys}がカラムとして存在しません。カラム: {list(subset.columns)[:20]}, インデックスタイプ: {type(subset.index)}")
            subset = subset.reset_index()
        return subset

    @staticmethod
    def _reset_index_if_multiindex(df: pd.DataFrame, target_original_index: pd.Index, merge_keys: list[str]) -> pd.DataFrame:
        """MultiIndexの場合にreset_indexを実行し、merge_keysがカラムとして存在することを確認"""
        if isinstance(df.index, pd.MultiIndex):
            return df.reset_index()
        if len(df) == 0:
            result = pd.DataFrame(columns=merge_keys, index=target_original_index)
            if isinstance(result.index, pd.MultiIndex): result = result.reset_index()
            return result
        if not isinstance(target_original_index, pd.MultiIndex):
            raise ValueError(f"dfのインデックスがMultiIndexではありません。index type: {type(df.index)}, index names: {df.index.names if hasattr(df.index, 'names') else 'N/A'}, columns: {df.columns.tolist()}")
        
        df = df.reindex(target_original_index)
        if not isinstance(df.index, pd.MultiIndex): raise ValueError(f"dfのインデックスがMultiIndexではありません（reindex後も）。index type: {type(df.index)}, index names: {df.index.names if hasattr(df.index, 'names') else 'N/A'}, columns: {df.columns.tolist()}")
        return df.reset_index()

    @staticmethod
    def _get_available_recent_race_columns(df: pd.DataFrame) -> list[str]:
        """DataFrameから直近レース抽出に使用可能なカラムを取得"""
        return [col for col in JockeyStatistics._REQUIRED_RECENT_RACE_COLUMNS if col in df.columns]

    @staticmethod
    def _calculate_time_series_stats(stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, prefix: str) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータのみを使って統計量を計算（未来情報を完全に除外）。"""
        merge_keys = JockeyStatistics.MERGE_KEYS
        target_original_index = target_df.index
        
        target_sorted = pd.DataFrame({group_col: target_df[group_col].values, time_col: target_df[time_col].values}, index=target_df.index)
        stats_df_clean = stats_df.dropna(subset=[group_col, time_col])
        target_sorted = target_sorted.dropna(subset=[group_col, time_col])
        stats_sorted = stats_df_clean.sort_values(by=[group_col, time_col])
        
        stats_sorted[f"{prefix}_cumsum_1st"] = stats_sorted.groupby(group_col)["rank_1st"].cumsum()
        stats_sorted[f"{prefix}_cumsum_3rd"] = stats_sorted.groupby(group_col)["rank_3rd"].cumsum()
        stats_sorted[f"{prefix}_cumsum_rank"] = stats_sorted.groupby(group_col)["着順"].cumsum()
        stats_sorted[f"{prefix}_cumcount"] = stats_sorted.groupby(group_col).cumcount() + 1
        
        grouped_stats = stats_sorted.groupby(group_col, sort=False)
        target_groups = set(target_sorted[group_col].unique())
        grouped_targets = target_sorted.groupby(group_col, sort=False)
        valid_groups = [g for g in target_groups if g in grouped_stats.groups and g in grouped_targets.groups]
        
        if len(valid_groups) == 0:
            empty_df = pd.DataFrame(columns=[group_col, time_col, f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd", f"{prefix}_cumsum_rank", f"{prefix}_cumcount"], index=target_original_index)
            if isinstance(empty_df.index, pd.MultiIndex): empty_df = empty_df.reset_index()
            return empty_df
        
        results = []
        with tqdm(total=len(valid_groups), desc=f"{prefix}グループ処理", leave=True, unit="groups") as pbar:
            for group_value in valid_groups:
                group_stats = grouped_stats.get_group(group_value)
                group_targets = grouped_targets.get_group(group_value)[[group_col, time_col]]
                result_df = JockeyStatistics._process_group_time_series_stats(group_value, group_stats, group_targets, group_col, time_col, prefix)
                if len(result_df) > 0: results.append(result_df)
                pbar.update(1)
        
        if results:
            merged = pd.concat([df for df in results if len(df) > 0])
            if not isinstance(merged.index, pd.MultiIndex) and len(merged) > 0: merged = merged.reindex(target_original_index)
        else:
            merged = pd.DataFrame(columns=[group_col, time_col, f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd", f"{prefix}_cumsum_rank", f"{prefix}_cumcount"], index=target_original_index)
        
        if len(merged) > 0:
            # cumcountが0の場合は0除算を防ぐ（新米騎手の初レースなど正常なケース）
            merged[f"{JockeyStatistics.JP_PREFIX}勝率"] = (merged[f"{JockeyStatistics.PREFIX}_cumsum_1st"] / merged[f"{JockeyStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{JockeyStatistics.JP_PREFIX}連対率"] = (merged[f"{JockeyStatistics.PREFIX}_cumsum_3rd"] / merged[f"{JockeyStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{JockeyStatistics.JP_PREFIX}平均着順"] = (merged[f"{JockeyStatistics.PREFIX}_cumsum_rank"] / merged[f"{JockeyStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{JockeyStatistics.JP_PREFIX}出走回数"] = merged[f"{JockeyStatistics.PREFIX}_cumcount"].fillna(0).astype(int)
        
        del target_sorted, stats_sorted, grouped_stats, grouped_targets
        
        merged = JockeyStatistics._reset_index_if_multiindex(merged, target_original_index, merge_keys)
        if not all(col in merged.columns for col in merge_keys): raise ValueError(f"mergedに{merge_keys}がカラムとして存在しません。columns: {merged.columns.tolist()}, index type: {type(merged.index)}, index names: {merged.index.names if hasattr(merged.index, 'names') else 'N/A'}")
        
        required_cols = [group_col, time_col, f"{JockeyStatistics.JP_PREFIX}勝率", f"{JockeyStatistics.JP_PREFIX}連対率", f"{JockeyStatistics.JP_PREFIX}平均着順", f"{JockeyStatistics.JP_PREFIX}出走回数"] + merge_keys
        return merged[[col for col in merged.columns if col in required_cols]]

    @staticmethod
    def _extract_recent_races(stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, num_races: int = 3, prefix: str = "jockey") -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータから直近Nレースの詳細情報を抽出（未来情報を完全に除外）。"""
        merge_keys = JockeyStatistics.MERGE_KEYS
        
        target_original_index = target_df.index
        available_cols = JockeyStatistics._get_available_recent_race_columns(stats_df)
        if not available_cols: raise ValueError("stats_dfに必要なカラムが存在しません。")
        
        stats_df_subset = pd.DataFrame({col: stats_df[col].values for col in [group_col, time_col] + available_cols})
        target_df_subset = pd.DataFrame({group_col: target_df[group_col].values, time_col: target_df[time_col].values}, index=target_df.index)
        
        grouped_stats = stats_df_subset.groupby(group_col, sort=False)
        target_groups = set(target_df_subset[group_col].unique())
        grouped_targets = target_df_subset.groupby(group_col, sort=False)
        valid_groups = [g for g in target_groups if g in grouped_stats.groups and g in grouped_targets.groups]
        
        prefix_jp = JockeyStatistics._PREFIX_JP_MAP.get(prefix)
        if not prefix_jp: raise ValueError(f"未知のprefix: {prefix}")
        
        if len(valid_groups) == 0:
            result_cols = [group_col, time_col] + [f"{prefix_jp}直近{i}{jp_col}" for i in range(1, num_races + 1) for jp_col in available_cols] + [f"{prefix_jp}直近{i}レースキー_SED" for i in range(1, num_races + 1)]
            result_df = pd.DataFrame(index=target_original_index, columns=result_cols)
            if isinstance(result_df.index, pd.MultiIndex): result_df = result_df.reset_index()
            return result_df
        
        results = []
        with tqdm(total=len(valid_groups), desc=f"{prefix}直近レース抽出", leave=True, unit="groups") as pbar:
            for group_value in valid_groups:
                group_stats = grouped_stats.get_group(group_value)
                group_targets = grouped_targets.get_group(group_value)[[group_col, time_col]]
                result_df = JockeyStatistics._process_group_recent_races(group_value, group_stats, group_targets, group_col, time_col, num_races, prefix)
                if len(result_df) > 0: results.append(result_df)
                pbar.update(1)
        
        result_df = pd.concat([df for df in results if len(df) > 0]) if results else pd.DataFrame()
        
        if len(result_df) == 0:
            result_cols = [group_col, time_col] + [f"{prefix_jp}直近{i}{jp_col}" for i in range(1, num_races + 1) for jp_col in available_cols] + [f"{prefix_jp}直近{i}レースキー_SED" for i in range(1, num_races + 1)]
            result_df = pd.DataFrame(index=target_original_index, columns=result_cols)
        
        result_df = JockeyStatistics._reset_index_if_multiindex(result_df, target_original_index, merge_keys)
        if not all(col in result_df.columns for col in merge_keys): raise ValueError(f"result_dfに{merge_keys}がカラムとして存在しません。columns: {result_df.columns.tolist()}, index type: {type(result_df.index)}, index names: {result_df.index.names if hasattr(result_df.index, 'names') else 'N/A'}")
        
        del stats_df_subset, target_df_subset, grouped_stats, grouped_targets
        gc.collect()
        
        return result_df

    @staticmethod
    def _process_group_time_series_stats(group_value, group_stats, group_targets, group_col, time_col, prefix):
        """グループごとの時系列統計量を計算（並列化用）"""
        group_stats = group_stats.sort_values(by=time_col).reset_index(drop=True)
        if len(group_stats) == 0 or len(group_targets) == 0: return pd.DataFrame()
        
        group_stats_times = group_stats[time_col].values
        group_targets_times = group_targets[time_col].values
        group_targets_indices = group_targets.index.values
        indices = np.searchsorted(group_stats_times, group_targets_times, side='left') - 1
        
        n_targets = len(group_targets)
        result_data = {group_col: [group_value] * n_targets, time_col: group_targets_times}
        result_index = group_targets_indices
        
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
        
        return pd.DataFrame(result_data, index=result_index)

    @staticmethod
    def _process_group_recent_races(group_value, group_stats, group_targets, group_col, time_col, num_races, prefix):
        """グループごとの直近レースを抽出（並列化用）"""
        group_stats = group_stats.sort_values(by=time_col).reset_index(drop=True)
        
        prefix_jp = JockeyStatistics._PREFIX_JP_MAP.get(prefix)
        if not prefix_jp: raise ValueError(f"未知のprefix: {prefix}")
        
        available_jp_columns = JockeyStatistics._get_available_recent_race_columns(group_stats)
        if not available_jp_columns: raise ValueError("stats_dfに必要なカラムが存在しません。")
        
        if len(group_stats) == 0 or len(group_targets) == 0:
            result_cols = [group_col, time_col] + [f"{prefix_jp}直近{i}{jp_col}" for i in range(1, num_races + 1) for jp_col in available_jp_columns] + [f"{prefix_jp}直近{i}レースキー_SED" for i in range(1, num_races + 1)]
            return pd.DataFrame(columns=result_cols)
        
        group_stats_times = group_stats[time_col].values
        group_targets_times = group_targets[time_col].values
        group_targets_indices = group_targets.index.values
        n_targets = len(group_targets)
        
        result_data = {group_col: np.full(n_targets, group_value), time_col: group_targets_times}
        result_index = group_targets_indices
        
        for i in range(1, num_races + 1):
            for jp_col in available_jp_columns: result_data[f"{prefix_jp}直近{i}{jp_col}"] = np.full(n_targets, np.nan, dtype=float)
            result_data[f"{prefix_jp}直近{i}レースキー_SED"] = np.full(n_targets, None, dtype=object)
        
        stats_arrays = {col: group_stats[col].values for col in available_jp_columns}
        race_key_array = group_stats["race_key"].values if "race_key" in group_stats.columns else None
        
        search_indices = np.searchsorted(group_stats_times, group_targets_times, side='left')
        
        for target_idx in range(n_targets):
            past_count = search_indices[target_idx]
            if past_count == 0: continue
            start_idx = max(0, past_count - num_races)
            recent_indices = np.arange(start_idx, past_count)
            for i in range(1, num_races + 1):
                race_idx_in_recent = len(recent_indices) - i
                if race_idx_in_recent < 0: continue
                race_idx = recent_indices[race_idx_in_recent]
                for jp_col in available_jp_columns: result_data[f"{prefix_jp}直近{i}{jp_col}"][target_idx] = stats_arrays[jp_col][race_idx]
                if race_key_array is not None: result_data[f"{prefix_jp}直近{i}レースキー_SED"][target_idx] = race_key_array[race_idx]
        
        return pd.DataFrame(result_data, index=result_index)
