#!/usr/bin/env python3
"""
包括的なデータリークチェックスクリプト

以下のリークを検証：
1. 前走データのリーク（prev_*_race_keyが現在のレースより後でないか）
2. 統計量のリーク（start_datetimeより前のデータのみ使用されているか）
3. 学習データとテストデータの時系列分割が正しいか
4. 特徴量が未来情報を含んでいないか
5. 平均順位誤差が異常に大きい原因の調査
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).resolve().parent.parent.parent  # tmp_scripts -> notebooks -> apps/prediction
sys.path.insert(0, str(project_root))

from src.data_processer import DataProcessor


def check_previous_race_leakage(df: pd.DataFrame) -> dict:
    """前走データのリークを検証（英語キーと日本語キーの両方に対応）"""
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
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in df_for_check.columns:
        warnings.append("start_datetimeカラムが存在しません（時系列比較ができません）")
        return {"issues": issues, "warnings": warnings, "valid": False}
    
    # 前走データのカラムを確認（英語キーと日本語キーの両方を確認）
    prev_race_key_cols_en = [f"prev_{i}_race_key" for i in range(1, 6)]
    prev_race_key_cols_jp = [f"前走{i}_race_key" for i in range(1, 6)]
    prev_race_key_cols = prev_race_key_cols_en + prev_race_key_cols_jp
    
    existing_prev_cols = [col for col in prev_race_key_cols if col in df_for_check.columns]
    
    if not existing_prev_cols:
        warnings.append("前走データのrace_keyカラムが見つかりません（前走データが抽出されていない可能性）")
        return {"issues": issues, "warnings": warnings, "valid": True}
    
    print(f"検証対象カラム: {existing_prev_cols}")
    
    # start_datetimeを数値に変換（YYYYMMDDHHMM形式を想定）
    if df_for_check["start_datetime"].dtype == "object":
        # 文字列の場合、数値に変換を試行
        df_for_check["start_datetime_numeric"] = pd.to_numeric(
            df_for_check["start_datetime"].astype(str).str.replace("-", "").str.replace(" ", "").str.replace(":", ""),
            errors="coerce"
        )
    else:
        df_for_check["start_datetime_numeric"] = df_for_check["start_datetime"]
    
    # 各前走データのrace_keyと対象レースのstart_datetimeを比較
    for col in existing_prev_cols:
        # 前走データが存在する行のみを対象
        mask = df_for_check[col].notna()
        if mask.sum() == 0:
            print(f"  ⚠️  {col}: データなし")
            continue
        
        prev_race_keys = df_for_check.loc[mask, col].astype(str)
        current_race_keys = df_for_check.loc[mask, "race_key"].astype(str)
        current_datetimes = df_for_check.loc[mask, "start_datetime_numeric"]
        
        # 前走レースのstart_datetimeを取得（race_keyから推測）
        # race_keyの形式: YYYYMMDD_XX_XX_XX_XX
        prev_datetimes = []
        for prev_race_key in prev_race_keys:
            if pd.isna(prev_race_key) or prev_race_key == "nan":
                prev_datetimes.append(np.nan)
            else:
                # race_keyから日付部分を抽出（YYYYMMDD）
                parts = str(prev_race_key).split("_")
                if len(parts) > 0 and len(parts[0]) >= 8:
                    try:
                        prev_date = int(parts[0][:8]) * 10000  # YYYYMMDD0000形式に変換
                        prev_datetimes.append(prev_date)
                    except:
                        prev_datetimes.append(np.nan)
                else:
                    prev_datetimes.append(np.nan)
        
        prev_datetimes = pd.Series(prev_datetimes, index=mask[mask].index)
        
        # 前走データのstart_datetimeが対象レースのstart_datetimeより後（または同じ）の場合、リーク
        valid_mask = prev_datetimes.notna() & current_datetimes.notna()
        if valid_mask.sum() == 0:
            warnings.append(f"{col}: 有効な日時データが存在しません")
            continue
        
        leak_mask = valid_mask & (prev_datetimes >= current_datetimes)
        leak_count = leak_mask.sum()
        
        if leak_count > 0:
            leak_indices = df_for_check.loc[mask][leak_mask].index[:10]  # 最初の10件を表示
            issues.append(f"{col}: {leak_count}件のリークを検出（前走レースの日付が現在のレースの日付より後または同じ）")
            print(f"  ❌ {col}: {leak_count}件のリークを検出")
            print(f"     サンプル（最初の10件）:")
            for idx in leak_indices:
                print(f"       - インデックス: {idx}")
                print(f"         対象レース: {df_for_check.loc[idx, 'race_key']}, start_datetime: {df_for_check.loc[idx, 'start_datetime']}")
                print(f"         前走: {df_for_check.loc[idx, col]}, 前走日時: {prev_datetimes.loc[idx]}")
        else:
            print(f"  ✅ {col}: リークなし（{valid_mask.sum():,}件検証）")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def check_statistics_leakage(df: pd.DataFrame) -> dict:
    """統計量のリークを検証（コードレビューとデータ検証の両方）"""
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
    """学習データとテストデータの分割が正しいか検証"""
    print("\n" + "=" * 80)
    print("【学習データとテストデータの分割検証】")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in train_df.columns or "start_datetime" not in test_df.columns:
        issues.append("start_datetimeカラムが存在しません（分割検証ができません）")
        return {"issues": issues, "warnings": warnings, "valid": False}
    
    # start_datetimeを数値に変換
    train_datetimes = pd.to_numeric(train_df["start_datetime"], errors="coerce")
    test_datetimes = pd.to_numeric(test_df["start_datetime"], errors="coerce")
    split_datetime = pd.to_datetime(split_date).strftime("%Y%m%d")
    split_datetime_numeric = int(split_datetime) * 10000  # YYYYMMDD0000形式
    
    # 学習データの最大日時
    train_max = train_datetimes.max()
    # テストデータの最小日時
    test_min = test_datetimes.min()
    
    print(f"分割日時: {split_date} ({split_datetime_numeric})")
    print(f"学習データ: {len(train_df):,}件, 最大日時: {train_max}")
    print(f"テストデータ: {len(test_df):,}件, 最小日時: {test_min}")
    
    # 学習データに分割日時より後のデータが含まれていないか
    train_after_split = (train_datetimes > split_datetime_numeric).sum()
    if train_after_split > 0:
        issues.append(f"学習データに分割日時より後のデータが{train_after_split}件含まれています")
        print(f"  ❌ 学習データに分割日時より後のデータが{train_after_split}件含まれています")
    else:
        print(f"  ✅ 学習データは分割日時より前のデータのみ")
    
    # テストデータに分割日時より前のデータが含まれていないか
    test_before_split = (test_datetimes < split_datetime_numeric).sum()
    if test_before_split > 0:
        issues.append(f"テストデータに分割日時より前のデータが{test_before_split}件含まれています")
        print(f"  ❌ テストデータに分割日時より前のデータが{test_before_split}件含まれています")
    else:
        print(f"  ✅ テストデータは分割日時より後のデータのみ")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def check_rank_error(df: pd.DataFrame) -> dict:
    """平均順位誤差が異常に大きい原因を調査"""
    print("\n" + "=" * 80)
    print("【平均順位誤差の異常値調査】")
    print("=" * 80)
    
    issues = []
    warnings = []
    
    # predicted_rankとrankが存在するか確認
    if "predicted_rank" not in df.columns or "rank" not in df.columns:
        warnings.append("predicted_rankまたはrankカラムが存在しません")
        return {"issues": issues, "warnings": warnings, "valid": True}
    
    # 順位誤差を計算
    df_check = df[["predicted_rank", "rank"]].copy()
    df_check = df_check.dropna()
    
    if len(df_check) == 0:
        warnings.append("predicted_rankとrankの両方が存在するデータがありません")
        return {"issues": issues, "warnings": warnings, "valid": True}
    
    df_check["rank_error"] = (df_check["predicted_rank"] - df_check["rank"]).abs()
    
    print(f"検証対象データ: {len(df_check):,}件")
    print(f"平均順位誤差: {df_check['rank_error'].mean():.2f}位")
    print(f"中央値順位誤差: {df_check['rank_error'].median():.2f}位")
    print(f"最大順位誤差: {df_check['rank_error'].max():.2f}位")
    print(f"最小順位誤差: {df_check['rank_error'].min():.2f}位")
    
    # 異常に大きい順位誤差を確認
    large_errors = df_check[df_check["rank_error"] > 100]
    if len(large_errors) > 0:
        issues.append(f"順位誤差が100位を超えるデータが{len(large_errors)}件存在します")
        print(f"  ❌ 順位誤差が100位を超えるデータが{len(large_errors)}件存在します")
        print(f"     サンプル（最初の10件）:")
        for idx in large_errors.index[:10]:
            print(f"       - インデックス: {idx}")
            print(f"         predicted_rank: {df_check.loc[idx, 'predicted_rank']}, rank: {df_check.loc[idx, 'rank']}, 誤差: {df_check.loc[idx, 'rank_error']}")
    else:
        print(f"  ✅ 順位誤差が100位を超えるデータはありません")
    
    # predicted_rankとrankの分布を確認
    print(f"\n  predicted_rankの統計:")
    print(f"    平均: {df_check['predicted_rank'].mean():.2f}")
    print(f"    中央値: {df_check['predicted_rank'].median():.2f}")
    print(f"    最大: {df_check['predicted_rank'].max():.2f}")
    print(f"    最小: {df_check['predicted_rank'].min():.2f}")
    
    print(f"\n  rankの統計:")
    print(f"    平均: {df_check['rank'].mean():.2f}")
    print(f"    中央値: {df_check['rank'].median():.2f}")
    print(f"    最大: {df_check['rank'].max():.2f}")
    print(f"    最小: {df_check['rank'].min():.2f}")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def main():
    """メイン処理"""
    print("=" * 80)
    print("包括的なデータリークチェック")
    print("=" * 80)
    
    # データ処理を実行（キャッシュから読み込むか、新規に処理）
    base_path = project_root.parent.parent  # apps/prediction -> apps -> umayomi
    data_processor = DataProcessor(base_path=base_path, use_cache=True)
    
    data_types = ["KYI", "BAC", "SED", "UKC", "TYB"]
    years = [2023, 2024]
    split_date = "2024-06-01"
    
    print(f"\nデータ処理を開始します...")
    print(f"  データタイプ: {data_types}")
    print(f"  年度: {years}")
    print(f"  分割日時: {split_date}")
    
    train_df, test_df, eval_df = data_processor.process_multiple_years(
        data_types=data_types,
        years=years,
        split_date=split_date
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
    
    # 4. 平均順位誤差の異常値調査（テストデータのみ）
    print("\n" + "=" * 80)
    print("平均順位誤差の異常値調査（テストデータ）")
    print("=" * 80)
    rank_error_result = check_rank_error(test_df)
    results["rank_error"] = rank_error_result
    
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


if __name__ == "__main__":
    main()

