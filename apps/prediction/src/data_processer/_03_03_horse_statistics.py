"""馬の過去成績統計を計算するクラス"""

from typing import Dict

import numpy as np
import pandas as pd
from tqdm import tqdm


class HorseStatistics:
    """馬の過去成績統計を計算するクラス"""
    
    # グループ化カラム
    GROUP_COLUMN = "血統登録番号"
    TIME_COLUMN = "start_datetime"
    
    # 統計量プレフィックス
    PREFIX = "horse"
    JP_PREFIX = "馬"

    @staticmethod
    def calculate(stats_df: pd.DataFrame, target_df: pd.DataFrame, schema: Dict) -> pd.DataFrame:
        """馬の過去成績統計特徴量を追加。各レースのstart_datetimeより前のデータのみを使用（未来情報を除外）。"""
        if HorseStatistics.GROUP_COLUMN not in target_df.columns:
            return target_df

        # race_keyと馬番のMultiIndexは_02_ステップで設定済み
        target_df_indexed = target_df

        target_df_sorted = target_df_indexed.sort_values(by=[HorseStatistics.GROUP_COLUMN, HorseStatistics.TIME_COLUMN])

        horse_stats = HorseStatistics._calculate_time_series_stats(
            stats_df, target_df_sorted, HorseStatistics.GROUP_COLUMN, HorseStatistics.TIME_COLUMN, HorseStatistics.PREFIX, schema
        )
        
        # スキーマからmerge_keysを取得
        if "joinKeys" not in schema: raise ValueError("スキーマにjoinKeysが定義されていません。スキーマファイルを確認してください。")
        merge_keys = schema["joinKeys"]

        # race_keyと馬番をキーとしてmerge（dropnaでインデックスが変わる可能性があるため）
        target_df_merged = target_df_sorted.reset_index()
        key_cols = [HorseStatistics.GROUP_COLUMN, HorseStatistics.TIME_COLUMN]
        horse_stats_subset = horse_stats[[col for col in horse_stats.columns if col not in key_cols]]
        # race_keyと馬番がカラムとして存在することを確認
        if not all(col in horse_stats_subset.columns for col in merge_keys):
            # インデックスがMultiIndexの場合、reset_indexで追加
            if isinstance(horse_stats_subset.index, pd.MultiIndex):
                horse_stats_subset = horse_stats_subset.reset_index()
            else:
                raise ValueError(f"horse_statsに{merge_keys}がカラムとして存在しません。")
        target_df_merged = target_df_merged.merge(
            horse_stats_subset,
            on=merge_keys,
            how="left",
            suffixes=("", "_horse_stats")
        )

        # 使用済みのDataFrameを削除
        del target_df_sorted, horse_stats, target_df_indexed

        # _03_feature_extractor.pyでmergeする際にrace_keyと馬番をカラムとして使用するため、reset_indexが必要
        return target_df_merged.reset_index()

    @staticmethod
    def _process_group_time_series_stats(
        group_value, group_stats, target_sorted, group_col, time_col, prefix
    ):
        """グループごとの時系列統計量を計算"""
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
    def _calculate_time_series_stats(
        stats_df: pd.DataFrame, target_df: pd.DataFrame, group_col: str, time_col: str, prefix: str, schema: Dict
    ) -> pd.DataFrame:
        """各レースのstart_datetimeより前のデータのみを使って統計量を計算（未来情報を完全に除外）。"""
        # スキーマからmerge_keysを取得
        if "joinKeys" not in schema: raise ValueError("スキーマにjoinKeysが定義されていません。スキーマファイルを確認してください。")
        merge_keys = schema["joinKeys"]
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
                result_df = HorseStatistics._process_group_time_series_stats(
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
            merged[f"{HorseStatistics.JP_PREFIX}勝率"] = (merged[f"{HorseStatistics.PREFIX}_cumsum_1st"] / merged[f"{HorseStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{HorseStatistics.JP_PREFIX}連対率"] = (merged[f"{HorseStatistics.PREFIX}_cumsum_3rd"] / merged[f"{HorseStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{HorseStatistics.JP_PREFIX}平均着順"] = (merged[f"{HorseStatistics.PREFIX}_cumsum_rank"] / merged[f"{HorseStatistics.PREFIX}_cumcount"]).fillna(0.0)
            merged[f"{HorseStatistics.JP_PREFIX}出走回数"] = merged[f"{HorseStatistics.PREFIX}_cumcount"].fillna(0).astype(int)
        
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
        if not all(col in merged.columns for col in merge_keys):
            raise ValueError(
                f"mergedに{merge_keys}がカラムとして存在しません。"
                f"columns: {merged.columns.tolist()}, "
                f"index type: {type(merged.index)}, "
                f"index names: {merged.index.names if hasattr(merged.index, 'names') else 'N/A'}"
            )
        
        # race_keyと馬番を含めて必要なカラムを選択
        required_cols = [
            group_col, time_col,
            f"{HorseStatistics.JP_PREFIX}勝率",
            f"{HorseStatistics.JP_PREFIX}連対率",
            f"{HorseStatistics.JP_PREFIX}平均着順",
            f"{HorseStatistics.JP_PREFIX}出走回数"
        ] + merge_keys
        if len(merged) > 0:
            result = merged[[col for col in merged.columns if col in required_cols]]
        else:
            # 空のDataFrameの場合でも、race_keyと馬番を含める
            result = pd.DataFrame(columns=merge_keys, index=target_original_index)
            if isinstance(result.index, pd.MultiIndex):
                result = result.reset_index()
        
        return result
