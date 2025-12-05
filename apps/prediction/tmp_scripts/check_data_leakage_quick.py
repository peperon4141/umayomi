"""
簡易データリークチェック（キャッシュから読み込んで高速にチェック）

実際に使用しているデータ（キャッシュ）でリークをチェック
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
base_project_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_project_path))

from src.data_processer import DataProcessor
from tmp_scripts.check_data_leakage import (
    check_previous_race_leakage,
    check_statistics_leakage,
    check_train_test_split,
)


def check_featured_df_leakage():
    """featured_df（日本語キー）で前走データのリークをチェック"""
    print("=" * 80)
    print("featured_df（日本語キー）での前走データリークチェック")
    print("=" * 80)
    
    # キャッシュからfeatured_dfを読み込み
    cache_dir = base_project_path / "cache"
    featured_cache = cache_dir / "BAC_KYI_SED_2024_featured.parquet"
    
    if not featured_cache.exists():
        print("キャッシュが見つかりません。train_rank_model_v1.pyを先に実行してください。")
        return None
    
    featured_df = pd.read_parquet(featured_cache)
    print(f"featured_df読み込み完了: {len(featured_df):,}件")
    
    # 前走データのrace_keyカラムを確認
    prev_race_key_cols = [f"prev_{i}_race_key" for i in range(1, 6)]
    existing_prev_cols = [col for col in prev_race_key_cols if col in featured_df.columns]
    
    print(f"前走データのrace_keyカラム: {existing_prev_cols}")
    
    if not existing_prev_cols:
        print("⚠️  前走データのrace_keyカラムが見つかりません")
        return None
    
    # リークチェック
    result = check_previous_race_leakage(featured_df)
    
    return result


def main():
    """メイン処理"""
    print("=" * 80)
    print("簡易データリークチェック（キャッシュから）")
    print("=" * 80)
    
    DATA_TYPES = ['BAC', 'KYI', 'SED']
    YEAR = 2024
    SPLIT_DATE = "2024-06-01"
    
    # DataProcessorでデータを読み込み（キャッシュから）
    data_processor = DataProcessor()
    
    print(f"\nデータ読み込み中（キャッシュから）...")
    print(f"  データタイプ: {DATA_TYPES}")
    print(f"  年度: {YEAR}")
    print(f"  分割日時: {SPLIT_DATE}")
    
    try:
        train_df, test_df, eval_df = data_processor.process(
            year=YEAR,
            split_date=SPLIT_DATE,
        )
        
        print(f"\nデータ読み込み完了:")
        print(f"  学習データ: {len(train_df):,}件")
        print(f"  テストデータ: {len(test_df):,}件")
        print(f"  評価用データ: {len(eval_df):,}件")
        
        # featured_dfでのリークチェック
        featured_result = check_featured_df_leakage()
        
        # 検証を実行
        results = {}
        
        # 1. 前走データのリーク検証
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
        split_result = check_train_test_split(train_df, test_df, SPLIT_DATE)
        results["train_test_split"] = split_result
        
        # 結果をまとめる
        print("\n" + "=" * 80)
        print("【検証結果サマリー】")
        print("=" * 80)
        
        all_issues = []
        all_warnings = []
        
        if featured_result:
            if featured_result.get("issues"):
                all_issues.extend([f"featured_df: {issue}" for issue in featured_result["issues"]])
            if featured_result.get("warnings"):
                all_warnings.extend([f"featured_df: {warning}" for warning in featured_result["warnings"]])
        
        for check_name, result in results.items():
            if result.get("issues"):
                all_issues.extend([f"{check_name}: {issue}" for issue in result["issues"]])
            if result.get("warnings"):
                all_warnings.extend([f"{check_name}: {warning}" for warning in result["warnings"]])
        
        if all_issues:
            print("\n❌ 検出された問題:")
            for issue in all_issues[:20]:
                print(f"  - {issue}")
            if len(all_issues) > 20:
                print(f"  ... 他{len(all_issues) - 20}件")
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
            print("\n【的中率が高い原因】")
            print("  データリークが検出されたため、モデルの的中率が異常に高い可能性が高いです。")
            return 1
        else:
            print("\n✅ データリークは検出されませんでした。")
            print("\n【的中率が高い他の可能性】")
            print("  1. テストデータが特定の期間・条件に偏っている可能性")
            print("  2. モデルが過学習している可能性")
            print("  3. 実際の運用時の的中率はより低い可能性が高い")
            return 0
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

