"""
完全なデータリークチェック

train_rank_model_v1.pyと同じ方法でデータを読み込み、リークをチェック
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import os

# プロジェクトルートをパスに追加
base_project_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_project_path))

# 並列処理を無効化（メモリ使用量削減）
os.environ["DATA_PROCESSER_MAX_WORKERS"] = "1"
os.environ["FEATURE_EXTRACTOR_MAX_WORKERS"] = "1"

from tmp_scripts.check_data_leakage import (
    check_previous_race_leakage,
    check_statistics_leakage,
    check_train_test_split,
)

from src.data_loader import load_multiple_npz_files
from src.data_processer.npz_loader import NpzLoader
from src.data_processer.jrdb_combiner import JrdbCombiner
from src.data_processer.feature_extractor import FeatureExtractor
from src.data_processer.key_converter import KeyConverter
from src.data_processer.time_series_splitter import TimeSeriesSplitter
from src.data_processer.column_selector import ColumnSelector


def main():
    """メイン処理"""
    print("=" * 80)
    print("完全なデータリークチェック")
    print("=" * 80)
    
    BASE_PATH = base_project_path / 'notebooks' / 'data'
    DATA_TYPES = ['BAC', 'KYI', 'SED']
    YEARS = [2023, 2024]
    split_date = "2024-06-01"
    
    print(f"\nデータ読み込み中...")
    print(f"  データタイプ: {DATA_TYPES}")
    print(f"  年度: {YEARS}")
    print(f"  分割日時: {split_date}")
    
    # 年度ごとに分割して処理（train_rank_model_v1.pyと同じ）
    featured_dfs = []
    for year in YEARS:
        print(f"\n{year}年のデータを処理中...")
        npz_loader = NpzLoader(BASE_PATH)
        year_data_dict = npz_loader.load(DATA_TYPES, year)
        
        jrdb_combiner = JrdbCombiner(base_project_path.parent.parent)
        raw_df = jrdb_combiner.combine(year_data_dict)
        
        feature_extractor = FeatureExtractor()
        sed_df = year_data_dict.get("SED")
        bac_df = year_data_dict.get("BAC")
        if sed_df is not None:
            featured_df = feature_extractor.extract_all_parallel(raw_df, sed_df, bac_df)
        else:
            featured_df = raw_df
        
        featured_dfs.append(featured_df)
        print(f"{year}年の特徴量抽出完了: {len(featured_df):,}件")
    
    # 年度ごとの特徴量抽出結果を結合
    featured_df = pd.concat(featured_dfs, ignore_index=True)
    print(f"\n結合完了: {len(featured_df):,}件")
    
    # データ変換
    key_converter = KeyConverter(base_project_path.parent.parent)
    converted_df = key_converter.convert(featured_df)
    converted_df = key_converter.optimize(converted_df)
    
    # インデックス設定
    if "race_key" in converted_df.columns:
        converted_df.set_index("race_key", inplace=True)
        if "start_datetime" in converted_df.columns:
            converted_df = converted_df.sort_values("start_datetime", ascending=True)
    
    # 時系列分割
    time_series_splitter = TimeSeriesSplitter()
    train_df, test_df = time_series_splitter.split(converted_df, split_date)
    
    # カラム選択
    column_selector = ColumnSelector(base_project_path.parent.parent)
    train_df = column_selector.select_training(train_df)
    test_df = column_selector.select_training(test_df)
    
    print(f"\nデータ読み込み完了:")
    print(f"  学習データ: {len(train_df):,}件")
    print(f"  テストデータ: {len(test_df):,}件")
    
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
    split_result = check_train_test_split(train_df, test_df, split_date)
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
        for issue in all_issues[:10]:  # 最初の10件のみ表示
            print(f"  - {issue}")
        if len(all_issues) > 10:
            print(f"  ... 他{len(all_issues) - 10}件")
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


if __name__ == "__main__":
    sys.exit(main())

