#!/usr/bin/env python3
"""
キャッシュからデータを読み込んでリークチェックを実行するスクリプト
特徴量抽出完了後のデータを使用してリークチェックを実行
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent.parent  # tmp_scripts -> notebooks -> apps/prediction
sys.path.insert(0, str(project_root))

from src.data_processer import DataProcessor
from tmp_scripts.check_leakage_comprehensive import (
    check_previous_race_leakage,
    check_statistics_leakage,
    check_train_test_split
)


def main():
    """メイン処理"""
    print("=" * 80)
    print("データリークチェック（キャッシュから読み込み）")
    print("=" * 80)
    
    # データ処理を実行（キャッシュから読み込む）
    base_path = project_root.parent.parent  # apps/prediction -> apps -> umayomi
    data_processor = DataProcessor(base_path=base_path, use_cache=True)
    
    data_types = ["KYI", "BAC", "SED", "UKC", "TYB"]
    years = [2024]
    split_date = "2024-06-01"
    
    print(f"\nデータ処理を開始します（キャッシュから読み込み）...")
    print(f"  データタイプ: {data_types}")
    print(f"  年度: {years}")
    print(f"  分割日時: {split_date}")
    
    try:
        train_df, test_df, eval_df = data_processor.process_multiple_years(
            data_types=data_types,
            years=years,
            split_date=split_date
        )
        
        print(f"\nデータ読み込み完了:")
        print(f"  学習データ: {len(train_df):,}件, 形状: {train_df.shape}")
        print(f"  テストデータ: {len(test_df):,}件, 形状: {test_df.shape}")
        print(f"  評価用データ: {len(eval_df):,}件, 形状: {eval_df.shape}")
        
        # 特徴量強化を実行（train_rank_model_v1.pyと同じ処理）
        from src.feature_enhancers import enhance_features
        
        print("\n特徴量強化を実行中...")
        race_key_col = "race_key"
        
        # race_keyがインデックスまたはカラムとして存在するか確認
        train_df_for_enhance = train_df.reset_index() if train_df.index.name == race_key_col else train_df.copy()
        test_df_for_enhance = test_df.reset_index() if test_df.index.name == race_key_col else test_df.copy()
        use_index = train_df.index.name == race_key_col
        
        # 特徴量強化を実行
        train_df_enhanced = enhance_features(train_df_for_enhance, race_key_col)
        test_df_enhanced = enhance_features(test_df_for_enhance, race_key_col)
        
        # インデックスを復元（必要に応じて）
        if use_index:
            train_df_enhanced = train_df_enhanced.set_index(race_key_col)
            test_df_enhanced = test_df_enhanced.set_index(race_key_col)
        
        print(f"特徴量強化完了: 学習={train_df_enhanced.shape}, テスト={test_df_enhanced.shape}")
        
        # 検証を実行
        results = {}
        
        # 1. 前走データのリーク検証（学習データとテストデータの両方）
        print("\n" + "=" * 80)
        print("学習データの前走データリーク検証")
        print("=" * 80)
        train_prev_result = check_previous_race_leakage(train_df_enhanced)
        results["train_previous_race"] = train_prev_result
        
        print("\n" + "=" * 80)
        print("テストデータの前走データリーク検証")
        print("=" * 80)
        test_prev_result = check_previous_race_leakage(test_df_enhanced)
        results["test_previous_race"] = test_prev_result
        
        # 2. 統計量のリーク検証
        print("\n" + "=" * 80)
        print("統計量のリーク検証（学習データ）")
        print("=" * 80)
        train_stat_result = check_statistics_leakage(train_df_enhanced)
        results["train_statistics"] = train_stat_result
        
        # 3. 学習データとテストデータの分割検証
        print("\n" + "=" * 80)
        print("学習データとテストデータの分割検証")
        print("=" * 80)
        split_result = check_train_test_split(train_df_enhanced, test_df_enhanced, split_date)
        results["train_test_split"] = split_result
        
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
        
        # 検証結果の詳細
        print("\n" + "=" * 80)
        print("【各検証項目の結果】")
        print("=" * 80)
        for check_name, result in results.items():
            status = "✅" if result.get("valid", False) else "❌"
            print(f"{status} {check_name}: {len(result.get('issues', []))}件の問題, {len(result.get('warnings', []))}件の警告")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()

