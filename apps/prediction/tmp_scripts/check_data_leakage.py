#!/usr/bin/env python3
"""
データリーク検証スクリプト

実際に生成されたデータを確認して、以下のリークがないかを検証：
1. 前走データのrace_keyが対象レースのrace_keyより前か
2. 統計量計算時に、対象レースを含めていないか
3. 学習データとテストデータの分割が正しく行われているか
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent.parent  # tmp_scripts -> notebooks -> apps/prediction
sys.path.insert(0, str(project_root))

from src.data_processer import DataProcessor

def check_previous_race_leakage(df: pd.DataFrame) -> dict:
    """前走データのリークを検証"""
    print("\n" + "=" * 80)
    print("【前走データのリーク検証】")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # race_keyがカラムまたはインデックスに存在するか確認
    df_for_check = df.copy()
    if df.index.name == "race_key":
        df_for_check = df_for_check.reset_index()
    elif "race_key" not in df_for_check.columns:
        issues.append("race_keyカラムが存在しません（カラムにもインデックスにも存在しない）")
        return {"issues": issues, "warnings": warnings, "valid": False}
    
    # 前走データのカラムを確認
    prev_race_key_cols = [f"prev_{i}_race_key" for i in range(1, 6)]
    existing_prev_cols = [col for col in prev_race_key_cols if col in df_for_check.columns]
    
    if not existing_prev_cols:
        warnings.append("前走データのrace_keyカラムが見つかりません（前走データが抽出されていない可能性）")
        return {"issues": issues, "warnings": warnings, "valid": True}
    
    print(f"検証対象カラム: {existing_prev_cols}")
    
    # 各前走データのrace_keyと対象レースのrace_keyを比較
    for col in existing_prev_cols:
        # 前走データが存在する行のみを対象
        mask = df_for_check[col].notna()
        if mask.sum() == 0:
            continue
        
        prev_race_keys = df_for_check.loc[mask, col].astype(str)
        current_race_keys = df_for_check.loc[mask, "race_key"].astype(str)
        
        # race_keyを数値として比較（YYYYMMDDHHMM形式を想定）
        # 文字列比較でも可（YYYYMMDD形式の場合）
        if len(prev_race_keys.iloc[0]) >= 8:
            prev_numeric = prev_race_keys.str[:8].astype(int)
            current_numeric = current_race_keys.str[:8].astype(int)
        else:
            prev_numeric = prev_race_keys.astype(int)
            current_numeric = current_race_keys.astype(int)
        
        # 前走データのrace_keyが対象レースのrace_keyより後（または同じ）の場合、リーク
        leak_mask = prev_numeric >= current_numeric
        leak_count = leak_mask.sum()
        
        if leak_count > 0:
            leak_indices = df_for_check.loc[mask][leak_mask].index[:10]  # 最初の10件を表示
            issues.append(f"{col}: {leak_count}件のリークを検出（前走データのrace_keyが対象レースのrace_keyより後または同じ）")
            print(f"  ❌ {col}: {leak_count}件のリークを検出")
            print(f"     サンプル（最初の10件）:")
            for idx in leak_indices:
                print(f"       - インデックス: {idx}, 対象レース: {df_for_check.loc[idx, 'race_key']}, 前走: {df_for_check.loc[idx, col]}")
        else:
            print(f"  ✅ {col}: リークなし")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}

def check_statistics_leakage(df: pd.DataFrame) -> dict:
    """統計量のリークを検証（統計量が対象レースを含めていないか）"""
    print("\n" + "=" * 80)
    print("【統計量のリーク検証】")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # 統計量カラムを確認（日本語キーと英語キーの両方を確認）
    stat_cols_jp = [
        "馬勝率", "馬連対率", "馬平均着順", "馬出走回数",
        "騎手勝率", "騎手連対率", "騎手平均着順", "騎手出走回数",
        "調教師勝率", "調教師連対率", "調教師平均着順", "調教師出走回数"
    ]
    stat_cols_en = [
        "horse_win_rate", "horse_place_rate", "horse_avg_rank", "horse_race_count",
        "jockey_win_rate", "jockey_place_rate", "jockey_avg_rank", "jockey_race_count",
        "trainer_win_rate", "trainer_place_rate", "trainer_avg_rank", "trainer_race_count"
    ]
    stat_cols = stat_cols_jp + stat_cols_en
    
    existing_stat_cols = [col for col in stat_cols if col in df.columns]
    
    if not existing_stat_cols:
        warnings.append("統計量カラムが見つかりません")
        return {"issues": issues, "warnings": warnings, "valid": True}
    
    print(f"検証対象カラム: {existing_stat_cols}")
    
    # 統計量がNaNでない行を確認
    for col in existing_stat_cols:
        non_null_count = df[col].notna().sum()
        print(f"  {col}: {non_null_count:,}件のデータが存在")
    
    # 統計量のリークは、実際のデータだけでは検証が難しいため、
    # コードレビューで確認する必要がある
    warnings.append("統計量のリークは、コードレビューで確認が必要です（start_datetimeによるフィルタリングが正しく実装されているか）")
    
    return {"issues": issues, "warnings": warnings, "valid": True}

def check_train_test_split(train_df: pd.DataFrame, test_df: pd.DataFrame, split_date: str) -> dict:
    """学習データとテストデータの分割を検証"""
    print("\n" + "=" * 80)
    print("【学習データとテストデータの分割検証】")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # start_datetimeが存在するか確認（カラムまたはインデックス）
    train_df_for_check = train_df.copy()
    test_df_for_check = test_df.copy()
    
    if train_df.index.name == "race_key":
        train_df_for_check = train_df_for_check.reset_index()
    if test_df.index.name == "race_key":
        test_df_for_check = test_df_for_check.reset_index()
    
    if "start_datetime" not in train_df_for_check.columns or "start_datetime" not in test_df_for_check.columns:
        issues.append("start_datetimeカラムが存在しません")
        return {"issues": issues, "warnings": warnings, "valid": False}
    
    # split_dateを数値に変換
    split_date_str = split_date.replace("-", "")
    if len(split_date_str) == 8:  # YYYYMMDD形式
        split_date_int = int(split_date_str) * 10000  # YYYYMMDDHHMM形式に変換（時刻は0000）
    else:
        issues.append(f"split_dateの形式が不正です: {split_date}")
        return {"issues": issues, "warnings": warnings, "valid": False}
    
    # 学習データのstart_datetimeがsplit_date以下か確認
    train_max_datetime = train_df_for_check["start_datetime"].max()
    train_over_split = (train_df_for_check["start_datetime"] > split_date_int).sum()
    
    if train_over_split > 0:
        issues.append(f"学習データに{split_date}より後のデータが{train_over_split}件含まれています")
        print(f"  ❌ 学習データの最大start_datetime: {train_max_datetime}")
        print(f"  ❌ split_dateより後のデータ: {train_over_split}件")
    else:
        print(f"  ✅ 学習データの最大start_datetime: {train_max_datetime}")
        print(f"  ✅ split_dateより後のデータ: 0件")
    
    # テストデータのstart_datetimeがsplit_dateより後か確認
    test_min_datetime = test_df_for_check["start_datetime"].min()
    test_before_split = (test_df_for_check["start_datetime"] <= split_date_int).sum()
    
    if test_before_split > 0:
        issues.append(f"テストデータに{split_date}以前のデータが{test_before_split}件含まれています")
        print(f"  ❌ テストデータの最小start_datetime: {test_min_datetime}")
        print(f"  ❌ split_date以前のデータ: {test_before_split}件")
    else:
        print(f"  ✅ テストデータの最小start_datetime: {test_min_datetime}")
        print(f"  ✅ split_date以前のデータ: 0件")
    
    # データの重複を確認
    if "race_key" in train_df_for_check.columns and "race_key" in test_df_for_check.columns:
        train_race_keys = set(train_df_for_check["race_key"].unique())
        test_race_keys = set(test_df_for_check["race_key"].unique())
        overlap = train_race_keys & test_race_keys
        
        if overlap:
            issues.append(f"学習データとテストデータに重複するrace_keyが{len(overlap)}件存在します")
            print(f"  ❌ 重複するrace_key: {len(overlap)}件")
            print(f"     サンプル（最初の10件）: {list(overlap)[:10]}")
        else:
            print(f"  ✅ 重複するrace_key: 0件")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}

def main():
    """メイン処理"""
    print("=" * 80)
    print("データリーク検証スクリプト")
    print("=" * 80)
    
    # データを読み込み
    base_project_path = Path(__file__).resolve().parent.parent.parent  # tmp_scripts -> notebooks -> apps/prediction
    BASE_PATH = base_project_path.parent.parent / "notebooks" / "data"
    base_path = base_project_path.parent.parent  # apps/prediction -> apps -> umayomi
    parquet_base_path = base_project_path / 'cache' / 'jrdb' / 'parquet'
    data_processor = DataProcessor(
        base_path=base_path,
        parquet_base_path=parquet_base_path
    )
    
    DATA_TYPES = ['BAC', 'KYI', 'SED']  # 最小限のデータタイプでチェック
    YEAR = 2024
    SPLIT_DATE = "2024-06-01"
    
    print(f"\nデータ読み込み中...")
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
        train_stat_result = check_statistics_leakage(train_df)
        results["train_statistics"] = train_stat_result
        
        # 3. 学習データとテストデータの分割検証
        split_result = check_train_test_split(train_df, test_df, SPLIT_DATE)
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
            return 1
        else:
            print("\n✅ データリークは検出されませんでした。")
            return 0
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
