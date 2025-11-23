"""
モデル評価用のユーティリティ
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd


def calculate_ndcg(y_true: np.ndarray, y_pred: np.ndarray, k: int = 3) -> float:
    """NDCGを計算"""

    def dcg(scores: np.ndarray, k: int) -> float:
        scores = np.asarray(scores)[:k]
        return np.sum(scores / np.log2(np.arange(2, len(scores) + 2)))

    # 実際の着順からスコアを生成（1着=3, 2着=2, 3着=1, その他=0）
    def convert_rank_to_score(rank: int) -> int:
        if rank == 1:
            return 3
        if rank == 2:
            return 2
        if rank == 3:
            return 1
        return 0

    # 予測順位でソート
    sorted_indices = np.argsort(-y_pred)
    sorted_scores = np.array([convert_rank_to_score(int(y_true[i])) for i in sorted_indices])

    # 理想的な順位（実際の着順順）
    ideal_scores = np.array(sorted([convert_rank_to_score(int(r)) for r in y_true], reverse=True))

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
    
    # rank列を数値型に変換（object型の場合があるため）
    predictions_df[rank_col] = pd.to_numeric(predictions_df[rank_col], errors="coerce")
    
    # rankが欠損している行を除外
    df = predictions_df[predictions_df[rank_col].notna()].copy()

    if len(df) == 0:
        raise ValueError("評価可能なデータがありません（rankがすべて欠損）")

    if race_key_col not in df.columns:
        raise ValueError(f"{race_key_col}カラムが見つかりません")

    results = {}

    # 1. NDCG@1, @2, @3（groupbyで最適化）
    ndcg_scores = {"ndcg@1": [], "ndcg@2": [], "ndcg@3": []}

    # race_key_colを数値型に変換（必要に応じて）
    if df[race_key_col].dtype == 'object':
        df[race_key_col] = df[race_key_col].astype(str)

    grouped = df.groupby(race_key_col)
    for race_key, race_data in grouped:
        if len(race_data) < 2:  # 1頭だけのレースはスキップ
            continue

        y_true = race_data[rank_col].values
        y_pred = race_data[predict_col].values

        for k in [1, 2, 3]:
            ndcg = calculate_ndcg(y_true, y_pred, k)
            ndcg_scores[f"ndcg@{k}"].append(ndcg)

    for k in [1, 2, 3]:
        scores = ndcg_scores[f"ndcg@{k}"]
        if scores:
            results[f"ndcg@{k}"] = np.mean(scores)
        else:
            results[f"ndcg@{k}"] = 0.0

    # 2. 1着的中率（groupbyで最適化）
    correct_1st = 0
    total_races = 0
    
    # デバッグ: 評価前の状態確認
    races_with_rank_1 = 0
    races_without_horse_num = 0

    grouped = df.groupby(race_key_col)
    for race_key, race_data in grouped:
        race_data_sorted = race_data.sort_values(predict_col, ascending=False)

        if horse_num_col not in race_data_sorted.columns:
            races_without_horse_num += 1
            continue

        # rank列を数値型に変換してから比較（浮動小数点数の問題を回避）
        if rank_col not in race_data_sorted.columns:
            continue  # rank列が存在しない場合はスキップ
        
        rank_values = pd.to_numeric(race_data_sorted[rank_col], errors='coerce')
        # 整数1と浮動小数点1.0の両方に対応
        actual_1st_mask = (rank_values == 1.0) | (rank_values == 1)

        if actual_1st_mask.any():
            races_with_rank_1 += 1
            total_races += 1
            predicted_1st_horse_num = race_data_sorted.iloc[0][horse_num_col]
            actual_1st_horse_num = race_data_sorted[actual_1st_mask].iloc[0][horse_num_col]

            if pd.notna(predicted_1st_horse_num) and pd.notna(actual_1st_horse_num):
                # 馬番も数値型に変換して比較
                predicted_1st_horse_num = pd.to_numeric(predicted_1st_horse_num, errors='coerce')
                actual_1st_horse_num = pd.to_numeric(actual_1st_horse_num, errors='coerce')
                if pd.notna(predicted_1st_horse_num) and pd.notna(actual_1st_horse_num):
                    if predicted_1st_horse_num == actual_1st_horse_num:
                        correct_1st += 1
    
    # デバッグ出力（最初の数レースのみ）
    if total_races == 0 and len(grouped) > 0:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[DEBUG] 1着的中率評価: 総レース数={len(grouped)}, rank==1のレース数={races_with_rank_1}, 馬番列なしレース数={races_without_horse_num}")
        # 最初のレースのサンプルを確認
        sample_race_key = list(grouped.groups.keys())[0]
        sample_race_data = grouped.get_group(sample_race_key)
        if rank_col in sample_race_data.columns:
            rank_values = pd.to_numeric(sample_race_data[rank_col], errors='coerce')
            logger.warning(f"[DEBUG] サンプルレース({sample_race_key})のrank値: {rank_values.dropna().tolist()[:10]}")
            logger.warning(f"[DEBUG] rank==1.0の行数: {len(sample_race_data[rank_values == 1.0])}")
            if horse_num_col in sample_race_data.columns:
                logger.warning(f"[DEBUG] 馬番列の有効値数: {sample_race_data[horse_num_col].notna().sum()}")

    if total_races > 0:
        results["accuracy_1st"] = correct_1st / total_races * 100
        results["correct_1st"] = correct_1st
        results["total_races"] = total_races
    else:
        results["accuracy_1st"] = 0.0
        results["correct_1st"] = 0
        results["total_races"] = 0

    # 3. 3着以内的中率（groupbyで最適化）
    correct_top3 = 0
    total_races_top3 = 0

    for race_key, race_data in grouped:
        race_data_sorted = race_data.sort_values(predict_col, ascending=False)

        if horse_num_col not in race_data_sorted.columns:
            continue

        # rank列を数値型に変換してから比較（浮動小数点数の問題を回避）
        rank_values = pd.to_numeric(race_data_sorted[rank_col], errors='coerce')
        # 整数と浮動小数点の両方に対応
        actual_top3_mask = rank_values.isin([1.0, 2.0, 3.0, 1, 2, 3])

        if actual_top3_mask.any():
            total_races_top3 += 1
            # 馬番も数値型に変換
            predicted_top3_horse_nums = set(pd.to_numeric(race_data_sorted.head(3)[horse_num_col], errors='coerce').dropna().astype(int).tolist())
            actual_top3_horse_nums = set(pd.to_numeric(race_data_sorted[actual_top3_mask][horse_num_col], errors='coerce').dropna().astype(int).tolist())

            if len(predicted_top3_horse_nums & actual_top3_horse_nums) > 0:
                correct_top3 += 1

    if total_races_top3 > 0:
        results["accuracy_top3"] = correct_top3 / total_races_top3 * 100
        results["correct_top3"] = correct_top3
    else:
        results["accuracy_top3"] = 0.0
        results["correct_top3"] = 0

    # 4. 平均順位誤差（ベクトル化）
    rank_errors = []
    
    # レースごとにグループ化して処理
    grouped = df.groupby(race_key_col)
    for race_key, race_data in grouped:
        race_data_sorted = race_data.sort_values(predict_col, ascending=False)
        valid_mask = race_data_sorted[rank_col].notna()
        if valid_mask.any():
            predicted_ranks = np.arange(1, len(race_data_sorted) + 1)
            actual_ranks = pd.to_numeric(race_data_sorted[rank_col], errors='coerce').values
            errors = np.abs(predicted_ranks[valid_mask.values] - actual_ranks[valid_mask.values])
            rank_errors.extend(errors.tolist())

    if rank_errors:
        results["mean_rank_error"] = np.mean(rank_errors)
    else:
        results["mean_rank_error"] = 0.0

    # 5. 単勝回収率（オッズデータがある場合、groupbyで最適化）
    if odds_col and odds_col in df.columns:
        total_investment = 0
        total_return = 0
        valid_races = 0

        for race_key, race_data in grouped:
            race_data_sorted = race_data.sort_values(predict_col, ascending=False)

            predicted_1st = race_data_sorted.iloc[0]

            # 必須カラムを明示的にチェック（fallback禁止）
            if odds_col not in predicted_1st.index:
                continue
            if pd.notna(predicted_1st[odds_col]):
                odds = float(predicted_1st[odds_col])
                if rank_col not in predicted_1st.index:
                    continue
                actual_rank = predicted_1st[rank_col]

                if pd.notna(actual_rank) and int(actual_rank) == 1:
                    total_return += odds * 100
                else:
                    total_return += 0

                total_investment += 100
                valid_races += 1

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
