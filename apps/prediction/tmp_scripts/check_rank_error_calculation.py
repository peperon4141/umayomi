"""
平均順位誤差の計算方法を検証

平均順位誤差が685516.45位と異常に大きい原因を調査
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
base_project_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_project_path))

from src.evaluator import evaluate_model


def analyze_rank_error_calculation(predictions_df: pd.DataFrame) -> None:
    """
    平均順位誤差の計算方法を分析
    """
    print("=" * 80)
    print("平均順位誤差の計算方法を分析")
    print("=" * 80)
    
    # 予測結果をレースごとにソート
    predictions_sorted = predictions_df.sort_values(["race_key", "predicted_score"], ascending=[True, False])
    predictions_sorted["predicted_rank"] = predictions_sorted.groupby("race_key").cumcount() + 1
    
    # サンプルレースを取得
    sample_races = predictions_sorted["race_key"].unique()[:10]
    
    print(f"\nサンプルレース数: {len(sample_races)}")
    
    rank_errors_all = []
    
    for race_key in sample_races:
        race_data = predictions_sorted[predictions_sorted["race_key"] == race_key]
        
        if "rank" not in race_data.columns:
            continue
        
        # 予測順位と実際の着順を取得
        predicted_ranks = race_data["predicted_rank"].values
        actual_ranks = pd.to_numeric(race_data["rank"], errors="coerce").values
        
        # 有効なデータのみを対象
        valid_mask = ~np.isnan(actual_ranks)
        if not valid_mask.any():
            continue
        
        predicted_ranks_valid = predicted_ranks[valid_mask]
        actual_ranks_valid = actual_ranks[valid_mask]
        
        # 異常値を除外（1以上、頭数以内の着順のみ）
        max_rank = len(actual_ranks)
        valid_filter = (actual_ranks_valid >= 1) & (actual_ranks_valid <= max_rank)
        
        if valid_filter.any():
            errors = np.abs(predicted_ranks_valid[valid_filter] - actual_ranks_valid[valid_filter])
            rank_errors_all.extend(errors.tolist())
            
            print(f"\nレース: {race_key}")
            print(f"  頭数: {len(race_data)}")
            print(f"  予測順位: {predicted_ranks_valid[valid_filter][:10]}")
            print(f"  実際の着順: {actual_ranks_valid[valid_filter][:10]}")
            print(f"  誤差: {errors[:10]}")
            print(f"  平均誤差: {np.mean(errors):.2f}")
            
            # 異常に大きい誤差があるか確認
            if np.max(errors) > 100:
                print(f"  ⚠️  異常に大きい誤差: {np.max(errors):.2f}")
                print(f"  予測順位の最大値: {np.max(predicted_ranks_valid[valid_filter])}")
                print(f"  実際の着順の最大値: {np.max(actual_ranks_valid[valid_filter])}")
    
    if rank_errors_all:
        print(f"\n全体の平均順位誤差: {np.mean(rank_errors_all):.2f}")
        print(f"全体の最大順位誤差: {np.max(rank_errors_all):.2f}")
        print(f"全体の中央値順位誤差: {np.median(rank_errors_all):.2f}")
        
        # 異常値の確認
        large_errors = [e for e in rank_errors_all if e > 100]
        if large_errors:
            print(f"\n⚠️  異常に大きい誤差（100以上）: {len(large_errors)}件")
            print(f"  最大誤差: {np.max(large_errors):.2f}")


if __name__ == "__main__":
    # キャッシュからデータを読み込み（簡易版）
    print("注意: このスクリプトは予測結果のDataFrameが必要です。")
    print("train_rank_model_v1.pyを実行してから、このスクリプトを実行してください。")
    print("\nまたは、予測結果のDataFrameを直接読み込んでください。")

