"""
train_rank_model_v1.pyと同じデータでデータリークチェックを実行

キャッシュから読み込んだデータでチェックするため、実際に使用しているデータと同じものを検証
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
base_project_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_project_path))

from tmp_scripts.check_data_leakage import (
    check_previous_race_leakage,
    check_statistics_leakage,
    check_train_test_split,
)


def main():
    """メイン処理 - train_rank_model_v1.pyと同じデータでチェック"""
    print("=" * 80)
    print("データリークチェック（train_rank_model_v1.pyと同じデータ）")
    print("=" * 80)
    
    # train_rank_model_v1.pyと同じ設定
    BASE_PATH = base_project_path / 'notebooks' / 'data'
    DATA_TYPES = ['BAC', 'KYI', 'SED']
    YEARS = [2023, 2024]
    split_date = "2024-06-01"
    
    # キャッシュからデータを読み込み（train_rank_model_v1.pyと同じ処理）
    from src.data_processer import DataProcessor
    
    data_processor = DataProcessor(base_path=base_project_path.parent.parent)
    
    # 2023と2024のデータを結合してチェック
    print("\nデータを読み込み中（キャッシュから）...")
    
    # 2024年のデータを読み込み
    train_df, test_df, eval_df = data_processor.process(
        data_types=DATA_TYPES,
        year=2024,
        split_date=split_date,
    )
    
    if train_df is None or test_df is None or eval_df is None:
        print("キャッシュが見つかりません。train_rank_model_v1.pyを先に実行してください。")
        return 1
    
    print(f"データ読み込み完了:")
    print(f"  学習データ: {len(train_df):,}件")
    print(f"  テストデータ: {len(test_df):,}件")
    print(f"  評価用データ: {len(eval_df):,}件")
    
    # 検証を実行
    results = {}
    
    # 1. 前走データのリーク検証（学習データとテストデータの両方）
    print("\n" + "=" * 80)
    print("学習データの前走データリーク検証")
    print("=" * 80)
    train_prev_result = check_previous_race_leakage(train_df)
    results["train_previous_race"] = train_prev_result
    
    print("\n" + "=" * 80)
    print("テストデータの前走データリーク検証")
    print("=" * 80)
    test_prev_result = check_previous_race_leakage(test_df)
    results["test_previous_race"] = test_prev_result
    
    # 2. 統計量のリーク検証
    print("\n" + "=" * 80)
    print("統計量のリーク検証")
    print("=" * 80)
    train_stat_result = check_statistics_leakage(train_df)
    results["train_statistics"] = train_stat_result
    
    # 3. 学習データとテストデータの分割検証
    print("\n" + "=" * 80)
    print("学習データとテストデータの分割検証")
    print("=" * 80)
    split_result = check_train_test_split(train_df, test_df, split_date)
    results["train_test_split"] = split_result
    
    # 4. 評価用データ（日本語キー）で前走データのリーク検証
    print("\n" + "=" * 80)
    print("評価用データ（日本語キー）の前走データリーク検証")
    print("=" * 80)
    eval_prev_result = check_previous_race_leakage(eval_df)
    results["eval_previous_race"] = eval_prev_result
    
    # 結果をまとめる
    print("\n" + "=" * 80)
    print("【検証結果サマリー】")
    print("=" * 80)
    
    all_issues = []
    all_warnings = []
    
    for check_name, result in results.items():
        if result.get("issues"):
            all_issues.extend([f"{check_name}: {issue}" for issue in result["issues"]])
        if result.get("warnings"):
            all_warnings.extend([f"{check_name}: {warning}" for warning in result["warnings"]])
    
    if all_issues:
        print("\n❌ 検出された問題:")
        for issue in all_issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 重大な問題は検出されませんでした")
    
    if all_warnings:
        print("\n⚠️  警告:")
        for warning in all_warnings:
            print(f"  - {warning}")
    
    # 最終判定
    has_critical_issues = len(all_issues) > 0
    if has_critical_issues:
        print("\n❌ データリークが検出されました。修正が必要です。")
        print("\n【的中率が高い原因の可能性】")
        print("  データリークが検出されたため、モデルの的中率が異常に高い可能性があります。")
        return 1
    else:
        print("\n✅ データリークは検出されませんでした。")
        print("\n【的中率が高い他の可能性】")
        print("  1. テストデータが特定の期間・条件に偏っている可能性")
        print("  2. モデルが過学習している可能性")
        print("  3. 実際の的中率はより低い可能性が高い")
        return 0


if __name__ == "__main__":
    sys.exit(main())

