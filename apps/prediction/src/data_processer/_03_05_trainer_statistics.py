"""調教師の過去成績統計を計算するクラス"""

from typing import Dict

import numpy as np
import pandas as pd
from tqdm import tqdm


class TrainerStatistics:
    """調教師の過去成績統計を計算するクラス"""

    # 直近レース抽出に使用するカラム（SEDデータに含まれるカラム）
    _REQUIRED_RECENT_RACE_COLUMNS = ["着順", "タイム", "馬場状態"]

    @staticmethod
    def calculate(stats_df: pd.DataFrame, target_df: pd.DataFrame, schema: Dict) -> pd.DataFrame:
        """調教師の過去成績統計特徴量と直近3レース詳細を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
        if TrainerStatistics.GROUP_COLUMN not in target_df.columns: return target_df

        # race_keyと馬番のMultiIndexは_02_ステップで設定済み
        target_df_indexed = target_df
        
        target_df_sorted = target_df_indexed.sort_values(by=[TrainerStatistics.GROUP_COLUMN, TrainerStatistics.TIME_COLUMN])

        trainer_stats = TrainerStatistics._calculate_time_series_stats(
            stats_df, target_df_sorted, TrainerStatistics.GROUP_COLUMN, TrainerStatistics.TIME_COLUMN, TrainerStatistics.PREFIX, schema
        )
        trainer_recent_races = TrainerStatistics._extract_recent_races(
            stats_df, target_df_sorted, TrainerStatistics.GROUP_COLUMN, TrainerStatistics.TIME_COLUMN, TrainerStatistics.RECENT_RACES_COUNT, TrainerStatistics.PREFIX, schema
        )

        # スキーマからmerge_keysを取得
        if "joinKeys" not in schema: raise ValueError("スキーマにjoinKeysが定義されていません。スキーマファイルを確認してください。")
        merge_keys = schema["joinKeys"]

        # race_keyと馬番をキーとしてmerge（dropnaでインデックスが変わる可能性があるため）
        target_df_merged = target_df_sorted.reset_index()
        key_cols = [TrainerStatistics.GROUP_COLUMN, TrainerStatistics.TIME_COLUMN]
        trainer_stats_subset = trainer_stats[[col for col in trainer_stats.columns if col not in key_cols]]
        # race_keyと馬番がカラムとして存在することを確認
        if not all(col in trainer_stats_subset.columns for col in merge_keys):
            # インデックスがMultiIndexの場合、reset_indexで追加
            if isinstance(trainer_stats_subset.index, pd.MultiIndex):
                trainer_stats_subset = trainer_stats_subset.reset_index()
            else:
                raise ValueError(f"trainer_statsに{merge_keys}がカラムとして存在しません。")
        target_df_merged = target_df_merged.merge(
            trainer_stats_subset,
            on=merge_keys,
            how="left",
            suffixes=("", "_trainer_stats")
        )

        # race_keyと馬番をキーとしてmerge
        trainer_recent_subset = trainer_recent_races[[col for col in trainer_recent_races.columns if col not in key_cols]]
        # race_keyと馬番がカラムとして存在することを確認
        if not all(col in trainer_recent_subset.columns for col in merge_keys):
            # インデックスがMultiIndexの場合、reset_indexで追加
            if isinstance(trainer_recent_subset.index, pd.MultiIndex):
                trainer_recent_subset = trainer_recent_subset.reset_index()
            else:
                raise ValueError(f"trainer_recent_racesに{merge_keys}がカラムとして存在しません。")
        target_df_merged = target_df_merged.merge(
            trainer_recent_subset,
            on=merge_keys,
            how="left",
            suffixes=("", "_trainer_recent")
        )

        # 使用済みのDataFrameを削除
        del target_df_sorted, trainer_stats, trainer_recent_races, target_df_indexed

        # _03_feature_extractor.pyでmergeする際にrace_keyと馬番をカラムとして使用するため、reset_indexが必要
        return target_df_merged.reset_index()

    @staticmethod
    def _get_available_recent_race_columns(df: pd.DataFrame) -> list[str]:
        """DataFrameから直近レース抽出に使用可能なカラムを取得"""
        return [col for col in TrainerStatistics._REQUIRED_RECENT_RACE_COLUMNS if col in df.columns]

    @staticmethod
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
        # race_keyと馬番のMultiIndexを使用
        group_targets_indices = group_targets.index.values
        indices = np.searchsorted(group_stats_times, group_targets_times, side='left') - 1
        
        n_targets = len(group_targets)
        result_data = {
            group_col: [group_value] * n_targets,
            time_col: group_targets_times,
        }
        # MultiIndexをDataFrameのインデックスとして使用
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
        
        result_df = pd.DataFrame(result_data, index=result_index)
        return result_df

    @staticmethod
    def _process_group_recent_races(
        group_value, group_stats, group_targets, group_col, time_col, num_races, prefix
    ):
        """グループごとの直近レースを抽出（並列化用）"""
        group_stats = group_stats.sort_values(by=time_col).reset_index(drop=True)
        
        available_jp_columns = TrainerStatistics._get_available_recent_race_columns(group_stats)
        if not available_jp_columns:
            raise ValueError("stats_dfに必要なカラムが存在しません。")
        
        if len(group_stats) == 0 or len(group_targets) == 0:
            result_cols = [group_col, time_col] + [
                f"{TrainerStatistics.JP_PREFIX}直近{i}{jp_col}"
                for i in range(1, num_races + 1)
                for jp_col in available_jp_columns
            ] + [
                f"{TrainerStatistics.JP_PREFIX}直近{i}race_key"  # 日程情報（リーク検証用）
                for i in range(1, num_races + 1)
            ]
            return pd.DataFrame(columns=result_cols)
        
        group_stats_times = group_stats[time_col].values
        group_targets_times = group_targets[time_col].values
        # race_keyと馬番のMultiIndexを使用
        group_targets_indices = group_targets.index.values
        n_targets = len(group_targets)
        
        result_data = {
            group_col: np.full(n_targets, group_value),
            time_col: group_targets_times,
        }
        # MultiIndexをDataFrameのインデックスとして使用
        result_index = group_targets_indices
        
        for i in range(1, num_races + 1):
            for jp_col in available_jp_columns:
                result_data[f"{TrainerStatistics.JP_PREFIX}直近{i}{jp_col}"] = np.full(n_targets, np.nan, dtype=float)
            # 日程情報（リーク検証用）
            result_data[f"{TrainerStatistics.JP_PREFIX}直近{i}race_key"] = np.full(n_targets, None, dtype=object)
        
        stats_arrays = {col: group_stats[col].values for col in available_jp_columns}
        
        # race_keyも取得（日程情報用）
        race_key_array = None
        if "race_key" in group_stats.columns:
            race_key_array = group_stats["race_key"].values
        
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
                        for jp_col in available_jp_columns:
                            result_data[f"{prefix_jp}直近{i}{jp_col}"][target_idx] = stats_arrays[jp_col][race_idx]
                        # 日程情報（リーク検証用）
                        if race_key_array is not None:
                            result_data[f"{prefix_jp}直近{i}race_key"][target_idx] = race_key_array[race_idx]
        
        result_df = pd.DataFrame(result_data, index=result_index)
        return result_df

    @staticmethod
    def _calculate_time_series_stats(
        stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, prefix: str
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータのみを使って統計量を計算（未来情報を完全に除外）。"""
        # race_keyと馬番のMultiIndexを使用
        target_original_index = target_df.index
        stats_sorted = stats_df.sort_values(by=[group_col, time_col])
        # 新しいDataFrameを直接作成（コピーを避ける）
        target_sorted = pd.DataFrame({
            group_col: target_df[group_col].values,
            time_col: target_df[time_col].values,
        }, index=target_df.index)
        
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
            empty_df = pd.DataFrame(columns=[group_col, time_col,
                                        f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd",
                                        f"{prefix}_cumsum_rank", f"{prefix}_cumcount"],
                              index=target_original_index)
            # インデックスがMultiIndexの場合、race_keyと馬番をカラムに追加
            if isinstance(empty_df.index, pd.MultiIndex):
                empty_df = empty_df.reset_index()
            return empty_df
        
        # シーケンシャル処理でメモリ使用量を削減
        results = []
        with tqdm(total=len(valid_groups), desc=f"{prefix}グループ処理", leave=True, unit="groups") as pbar:
            for group_value in valid_groups:
                group_stats = grouped_stats.get_group(group_value)
                result_df = TrainerStatistics._process_group_time_series_stats(
                    group_value, group_stats, target_sorted, group_col, time_col, prefix
                )
                if len(result_df) > 0:
                    results.append(result_df)
                pbar.update(1)
        
        if results:
            merged = pd.concat([df for df in results if len(df) > 0])
            # pd.concatの結果がMultiIndexでない場合、target_original_indexを使ってreindex
            if not isinstance(merged.index, pd.MultiIndex) and len(merged) > 0:
                merged = merged.reindex(target_original_index)
        else:
            # resultsが空の場合、target_original_indexを使用して空のDataFrameを作成
            merged = pd.DataFrame(
                columns=[group_col, time_col,
                        f"{prefix}_cumsum_1st", f"{prefix}_cumsum_3rd",
                        f"{prefix}_cumsum_rank", f"{prefix}_cumcount"],
                index=target_original_index
            )
        
        # 空のDataFrameの場合は列を追加しない
        if len(merged) > 0:
            merged[f"{TrainerStatistics.JP_PREFIX}勝率"] = (merged[f"{TrainerStatistics.PREFIX}_cumsum_1st"] / merged[f"{TrainerStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{TrainerStatistics.JP_PREFIX}連対率"] = (merged[f"{TrainerStatistics.PREFIX}_cumsum_3rd"] / merged[f"{TrainerStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{TrainerStatistics.JP_PREFIX}平均着順"] = (merged[f"{TrainerStatistics.PREFIX}_cumsum_rank"] / merged[f"{TrainerStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{TrainerStatistics.JP_PREFIX}出走回数"] = merged[f"{TrainerStatistics.PREFIX}_cumcount"].fillna(0).astype(int)
        
        # 使用済みのDataFrameを削除
        del target_sorted, stats_sorted, grouped_stats
        
        # まずreset_index()でrace_keyと馬番をカラムに追加してから、必要なカラムを選択
        if isinstance(merged.index, pd.MultiIndex):
            merged = merged.reset_index()
        elif len(merged) > 0:
            # MultiIndexでない場合でも、target_original_indexがMultiIndexならreindexでMultiIndexに変換
            if isinstance(target_original_index, pd.MultiIndex):
                merged = merged.reindex(target_original_index)
                if isinstance(merged.index, pd.MultiIndex):
                    merged = merged.reset_index()
                else:
                    raise ValueError(
                        f"mergedのインデックスがMultiIndexではありません（reindex後も）。"
                        f"index type: {type(merged.index)}, "
                        f"index names: {merged.index.names if hasattr(merged.index, 'names') else 'N/A'}, "
                        f"columns: {merged.columns.tolist()}"
                    )
            else:
                raise ValueError(
                    f"mergedのインデックスがMultiIndexではありません。"
                    f"index type: {type(merged.index)}, "
                    f"index names: {merged.index.names if hasattr(merged.index, 'names') else 'N/A'}, "
                    f"columns: {merged.columns.tolist()}"
                )
        
        # race_keyと馬番がカラムとして存在することを確認
        if "race_key" not in merged.columns or "馬番" not in merged.columns:
            raise ValueError(
                f"mergedにrace_keyと馬番がカラムとして存在しません。"
                f"columns: {merged.columns.tolist()}, "
                f"index type: {type(merged.index)}, "
                f"index names: {merged.index.names if hasattr(merged.index, 'names') else 'N/A'}"
            )
        
        # race_keyと馬番を含めて必要なカラムを選択
        if len(merged) > 0:
            result = merged[[col for col in merged.columns if col in [group_col, time_col, f"{prefix_jp}勝率", f"{prefix_jp}連対率", f"{prefix_jp}平均着順", f"{prefix_jp}出走回数", "race_key", "馬番"]]]
        else:
            # 空のDataFrameの場合でも、race_keyと馬番を含める
            result = merged[["race_key", "馬番"]]
        
        return result

    @staticmethod
    def _extract_recent_races(
        stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, num_races: int = 3, prefix: str = "trainer", schema: Dict = None
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータから直近Nレースの詳細情報を抽出（未来情報を完全に除外）。"""
        # スキーマからmerge_keysを取得
        if schema is None: raise ValueError("スキーマが提供されていません。")
        if "joinKeys" not in schema: raise ValueError("スキーマにjoinKeysが定義されていません。スキーマファイルを確認してください。")
        merge_keys = schema["joinKeys"]
        target_original_index = target_df.index
        available_cols = TrainerStatistics._get_available_recent_race_columns(stats_df)
        if not available_cols:
            raise ValueError("stats_dfに必要なカラムが存在しません。")
        
        stats_df_subset = pd.DataFrame({
            col: stats_df[col].values for col in [group_col, time_col] + available_cols
        })
        target_df_subset = pd.DataFrame({
            group_col: target_df[group_col].values,
            time_col: target_df[time_col].values,
        }, index=target_df.index)
        
        grouped_stats = stats_df_subset.groupby(group_col, sort=False)
        target_groups = set(target_df_subset[group_col].unique())
        grouped_targets = target_df_subset.groupby(group_col, sort=False)
        valid_groups = [g for g in target_groups if g in grouped_stats.groups and g in grouped_targets.groups]
        
        prefix_jp = {"horse": "馬", "jockey": "騎手", "trainer": "調教師"}.get(prefix)
        if not prefix_jp:
            raise ValueError(f"未知のprefix: {prefix}")
        
        if len(valid_groups) == 0:
            result_cols = [group_col, time_col] + [
                f"{prefix_jp}直近{i}{jp_col}"
                for i in range(1, num_races + 1)
                for jp_col in available_cols
            ] + [
                f"{prefix_jp}直近{i}race_key"
                for i in range(1, num_races + 1)
            ]
            return pd.DataFrame(index=target_original_index, columns=result_cols)
        
        # シーケンシャル処理でメモリ使用量を削減
        results = []
        with tqdm(total=len(valid_groups), desc=f"{prefix}直近レース抽出", leave=True, unit="groups") as pbar:
            for group_value in valid_groups:
                group_stats = grouped_stats.get_group(group_value)
                group_targets = grouped_targets.get_group(group_value)[[group_col, time_col]]
                result_df = TrainerStatistics._process_group_recent_races(
                    group_value, group_stats, group_targets, group_col, time_col, num_races, prefix
                )
                if len(result_df) > 0:
                    results.append(result_df)
                pbar.update(1)
        
        result_df = pd.concat([df for df in results if len(df) > 0]) if results else pd.DataFrame()
        
        # result_dfのインデックスはtarget_df_subsetのインデックス（target_original_index）と一致しているため、reindexは不要
        if len(result_df) == 0:
            result_cols = [group_col, time_col] + [
                f"{prefix_jp}直近{i}{jp_col}"
                for i in range(1, num_races + 1)
                for jp_col in available_cols
            ] + [
                f"{prefix_jp}直近{i}race_key"
                for i in range(1, num_races + 1)
            ]
            result_df = pd.DataFrame(index=target_original_index, columns=result_cols)
        
        # インデックスがMultiIndexの場合、race_keyと馬番をカラムに追加
        if isinstance(result_df.index, pd.MultiIndex) and result_df.index.names == ["race_key", "馬番"]:
            result_df = result_df.reset_index()
        elif isinstance(result_df.index, pd.MultiIndex):
            # MultiIndexだが名前が異なる場合、reset_indexで追加
            result_df = result_df.reset_index()
        
        del stats_df_subset, target_df_subset, grouped_stats, grouped_targets
        return result_df
