"""
モデル評価用のユーティリティ
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd


def calculate_ndcg(y_true: np.ndarray, y_pred: np.ndarray, k: int = 3) -> float:
    """NDCGを計算（ベクトル化）"""

    def dcg(scores: np.ndarray, k: int) -> float:
        scores = np.asarray(scores)[:k]
        return np.sum(scores / np.log2(np.arange(2, len(scores) + 2)))

    # ベクトル化：着順からスコアを生成（1着=3, 2着=2, 3着=1, その他=0）
    y_true_int = y_true.astype(int)
    scores = np.where(y_true_int == 1, 3, np.where(y_true_int == 2, 2, np.where(y_true_int == 3, 1, 0)))

    # 予測順位でソート
    sorted_indices = np.argsort(-y_pred)
    sorted_scores = scores[sorted_indices]

    # 理想的な順位（実際の着順順）
    ideal_scores = np.sort(scores)[::-1]

    dcg_score = dcg(sorted_scores, k)
    idcg_score = dcg(ideal_scores, k)

    if idcg_score == 0:
        return 0.0

    return dcg_score / idcg_score


def evaluate_model(
    predictions_df: pd.DataFrame,
    race_key_col: str = "race_key",
    rank_col: str = "rank",
    predict_col: str = "predict",
    horse_num_col: str = "馬番",
    odds_col: Optional[str] = None,
) -> Dict[str, float]:
    """
    モデル評価を実行
    
    注意: rank_colが存在しない場合、着順からrankを生成します
    """
    """
    モデル評価を実行

    Args:
        predictions_df: 予測結果のDataFrame（race_key, rank, predict, 馬番を含む）
        race_key_col: レースキーのカラム名
        rank_col: 実際の着順のカラム名
        predict_col: 予測値のカラム名
        horse_num_col: 馬番のカラム名
        odds_col: 確定単勝オッズのカラム名（オプション、回収率計算用）

    Returns:
        評価結果の辞書
    """
    # rank列が存在しない場合、着順から生成
    predictions_df = predictions_df.copy()
    if rank_col not in predictions_df.columns:
        if "着順" in predictions_df.columns:
            predictions_df[rank_col] = pd.to_numeric(predictions_df["着順"], errors="coerce")
        else:
            raise ValueError(f"{rank_col}列または着順列が見つかりません")
    
    # 事前に型変換（一度だけ）
    predictions_df[rank_col] = pd.to_numeric(predictions_df[rank_col], errors="coerce")
    if horse_num_col in predictions_df.columns:
        predictions_df[horse_num_col] = pd.to_numeric(predictions_df[horse_num_col], errors="coerce")
    
    # rankが欠損している行を除外
    df = predictions_df[predictions_df[rank_col].notna()].copy()
    
    # 全体を一度だけソート（race_keyとpredict_colで）
    df = df.sort_values([race_key_col, predict_col], ascending=[True, False])

    if len(df) == 0:
        raise ValueError("評価可能なデータがありません（rankがすべて欠損）")

    if race_key_col not in df.columns:
        raise ValueError(f"{race_key_col}カラムが見つかりません")

    results = {}

    # race_key_colを数値型に変換（必要に応じて）
    if df[race_key_col].dtype == 'object':
        df[race_key_col] = df[race_key_col].astype(str)

    # 事前にNumPy配列を取得（高速化のため）
    rank_values_all = df[rank_col].values
    predict_values_all = df[predict_col].values
    if horse_num_col in df.columns:
        horse_num_values_all = df[horse_num_col].values
    else:
        horse_num_values_all = None
    if odds_col and odds_col in df.columns:
        odds_values_all = df[odds_col].values
    else:
        odds_values_all = None

    # groupbyを1回だけ実行して全ての評価指標を計算（sort=Falseで高速化）
    grouped = df.groupby(race_key_col, sort=False)
    
    # 初期化
    ndcg_scores = {"ndcg@1": [], "ndcg@2": [], "ndcg@3": []}
    correct_1st = 0
    total_races = 0
    races_with_rank_1 = 0
    races_without_horse_num = 0
    correct_top3 = 0
    total_races_top3 = 0
    rank_errors_list = []
    total_investment = 0
    total_return = 0
    valid_races = 0

    for race_key, race_data in grouped:
        if len(race_data) < 2:  # 1頭だけのレースはスキップ
            continue

        # インデックスを使ってNumPy配列から直接取得（DataFrame操作を避ける）
        # race_dataの最初のインデックスがdf内のどこにあるかを取得
        first_idx = race_data.index[0]
        start_pos = df.index.get_loc(first_idx)
        if isinstance(start_pos, slice):
            start_idx = start_pos.start
        elif isinstance(start_pos, np.ndarray):
            start_idx = start_pos[0]
        else:
            start_idx = int(start_pos)
        end_idx = start_idx + len(race_data)

        # NumPy配列から直接取得
        y_true = rank_values_all[start_idx:end_idx]
        y_pred = predict_values_all[start_idx:end_idx]
        rank_values = y_true

        # 1. NDCG@1, @2, @3
        for k in [1, 2, 3]:
            ndcg = calculate_ndcg(y_true, y_pred, k)
            ndcg_scores[f"ndcg@{k}"].append(ndcg)

        # 2. 1着的中率（NumPy配列で直接処理）
        if horse_num_values_all is not None:
            race_horse_nums = horse_num_values_all[start_idx:end_idx]
            actual_1st_mask = (rank_values == 1.0) | (rank_values == 1)
            if actual_1st_mask.any():
                races_with_rank_1 += 1
                total_races += 1
                predicted_1st_horse_num = race_horse_nums[0]
                actual_1st_horse_num = race_horse_nums[actual_1st_mask][0]
                if pd.notna(predicted_1st_horse_num) and pd.notna(actual_1st_horse_num):
                    if predicted_1st_horse_num == actual_1st_horse_num:
                        correct_1st += 1
        else:
            races_without_horse_num += 1

        # 3. 3着以内的中率（NumPy配列で直接処理）
        if horse_num_values_all is not None:
            race_horse_nums = horse_num_values_all[start_idx:end_idx]
            actual_top3_mask = (rank_values >= 1) & (rank_values <= 3)
            if actual_top3_mask.any():
                total_races_top3 += 1
                # 予測上位3頭（既にソート済みなので最初の3つ）
                predicted_top3_horse_nums = race_horse_nums[:3]
                predicted_top3_valid = predicted_top3_horse_nums[~np.isnan(predicted_top3_horse_nums)].astype(int)
                # 実際の3着以内
                actual_top3_horse_nums = race_horse_nums[actual_top3_mask]
                actual_top3_valid = actual_top3_horse_nums[~np.isnan(actual_top3_horse_nums)].astype(int)
                if len(predicted_top3_valid) > 0 and len(actual_top3_valid) > 0:
                    if np.intersect1d(predicted_top3_valid, actual_top3_valid).size > 0:
                        correct_top3 += 1

        # 4. 平均順位誤差
        valid_mask = ~np.isnan(rank_values)
        if valid_mask.any():
            predicted_ranks = np.arange(1, len(rank_values) + 1)
            actual_ranks = rank_values[valid_mask]
            predicted_ranks_valid = predicted_ranks[valid_mask]
            
            max_rank = len(rank_values)
            valid_filter = (actual_ranks >= 1) & (actual_ranks <= max_rank * 2)
            if valid_filter.any():
                errors = np.abs(predicted_ranks_valid[valid_filter] - actual_ranks[valid_filter])
                rank_errors_list.append(errors)

        # 5. 単勝回収率（NumPy配列で直接処理）
        if odds_values_all is not None:
            race_odds = odds_values_all[start_idx:end_idx]
            race_rank_first = rank_values[0]
            
            if pd.notna(race_odds[0]) and pd.notna(race_rank_first):
                odds = float(race_odds[0])
                if int(race_rank_first) == 1:
                    total_return += odds * 100
                total_investment += 100
                valid_races += 1

    # rank_errorsを一度に結合
    if rank_errors_list:
        rank_errors = np.concatenate(rank_errors_list)
    else:
        rank_errors = np.array([])

    # 結果を集計
    for k in [1, 2, 3]:
        scores = ndcg_scores[f"ndcg@{k}"]
        if scores:
            results[f"ndcg@{k}"] = np.mean(scores)
        else:
            results[f"ndcg@{k}"] = 0.0

    if total_races > 0:
        results["accuracy_1st"] = correct_1st / total_races * 100
        results["correct_1st"] = correct_1st
        results["total_races"] = total_races
    else:
        results["accuracy_1st"] = 0.0
        results["correct_1st"] = 0
        results["total_races"] = 0

    # デバッグ出力（最初の数レースのみ）
    if total_races == 0 and len(grouped) > 0:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[DEBUG] 1着的中率評価: 総レース数={len(grouped)}, rank==1のレース数={races_with_rank_1}, 馬番列なしレース数={races_without_horse_num}")
        sample_race_key = list(grouped.groups.keys())[0]
        sample_race_data = grouped.get_group(sample_race_key)
        if rank_col in sample_race_data.columns:
            rank_values = pd.to_numeric(sample_race_data[rank_col], errors='coerce')
            logger.warning(f"[DEBUG] サンプルレース({sample_race_key})のrank値: {rank_values.dropna().tolist()[:10]}")
            logger.warning(f"[DEBUG] rank==1.0の行数: {len(sample_race_data[rank_values == 1.0])}")
            if horse_num_col in sample_race_data.columns:
                logger.warning(f"[DEBUG] 馬番列の有効値数: {sample_race_data[horse_num_col].notna().sum()}")

    if total_races_top3 > 0:
        results["accuracy_top3"] = correct_top3 / total_races_top3 * 100
        results["correct_top3"] = correct_top3
    else:
        results["accuracy_top3"] = 0.0
        results["correct_top3"] = 0

    if len(rank_errors) > 0:
        results["mean_rank_error"] = np.mean(rank_errors)
    else:
        results["mean_rank_error"] = 0.0

    if odds_col and odds_col in df.columns:
        if valid_races > 0 and total_investment > 0:
            results["recovery_rate"] = (total_return / total_investment) * 100
            results["total_investment"] = total_investment
            results["total_return"] = total_return
            results["valid_races"] = valid_races
        else:
            results["recovery_rate"] = 0.0
            results["total_investment"] = 0
            results["total_return"] = 0
            results["valid_races"] = 0
    else:
        results["recovery_rate"] = None
        results["total_investment"] = None
        results["total_return"] = None
        results["valid_races"] = None

    return results


def print_evaluation_results(results: Dict[str, float]) -> None:
    """評価結果を整形して表示"""
    print("\n" + "=" * 60)
    print("モデル評価結果")
    print("=" * 60)

    # NDCG
    print("\nNDCG（Normalized Discounted Cumulative Gain）:")
    for k in [1, 2, 3]:
        ndcg = results.get(f"ndcg@{k}", 0.0)
        print(f"  NDCG@{k}: {ndcg:.4f}")

    # 1着的中率
    accuracy_1st = results.get("accuracy_1st", 0.0)
    correct_1st = results.get("correct_1st", 0)
    total_races = results.get("total_races", 0)
    print(f"\n1着的中率: {accuracy_1st:.2f}% ({correct_1st}/{total_races}レース)")

    # 3着以内的中率
    accuracy_top3 = results.get("accuracy_top3", 0.0)
    correct_top3 = results.get("correct_top3", 0)
    print(f"3着以内的中率: {accuracy_top3:.2f}% ({correct_top3}/{total_races}レース)")

    # 平均順位誤差
    mean_error = results.get("mean_rank_error", 0.0)
    print(f"\n平均順位誤差: {mean_error:.2f}位")

    # 単勝回収率
    recovery_rate = results.get("recovery_rate")
    if recovery_rate is not None:
        total_investment = results.get("total_investment", 0)
        total_return = results.get("total_return", 0)
        valid_races = results.get("valid_races", 0)
        print(f"\n単勝回収率: {recovery_rate:.2f}%")
        print(f"  総投資額: {total_investment:,}円 ({valid_races}レース)")
        print(f"  総払戻額: {total_return:,.0f}円")
        print(f"  収益: {total_return - total_investment:,.0f}円")
