"""
各レース内の前走レース情報が、レース日よりも過去かを確認

前走データのrace_keyと現在のレースのrace_keyを比較して、
前走レースが現在のレースより過去であることを確認
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
base_project_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_project_path))

from src.data_processer.npz_loader import NpzLoader
from src.data_processer.jrdb_combiner import JrdbCombiner
from src.data_processer.feature_extractor import FeatureExtractor


def check_previous_race_dates(df: pd.DataFrame) -> dict:
    """
    前走レースの日付が現在のレースの日付よりも過去かを確認
    
    Args:
        df: featured_df（日本語キー、前走データを含む）
    
    Returns:
        検証結果の辞書
    """
    issues = []
    warnings = []
    valid_count = 0
    invalid_count = 0
    
    # race_keyとstart_datetimeが存在するか確認
    if "race_key" not in df.columns:
        return {"issues": ["race_keyカラムが見つかりません"], "warnings": [], "valid": False, "valid_count": 0, "invalid_count": 0}
    
    if "start_datetime" not in df.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False, "valid_count": 0, "invalid_count": 0}
    
    # 前走データのrace_keyカラムを確認
    prev_race_key_cols = [f"prev_{i}_race_key" for i in range(1, 6)]
    existing_prev_cols = [col for col in prev_race_key_cols if col in df.columns]
    
    if not existing_prev_cols:
        warnings.append("前走データのrace_keyカラムが見つかりません")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0, "valid_count": 0, "invalid_count": 0}
    
    print(f"検証対象カラム: {existing_prev_cols}")
    
    # サンプルサイズを制限（メモリ使用量削減）
    sample_size = min(10000, len(df))
    df_sample = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
    
    print(f"サンプルサイズ: {len(df_sample):,}件")
    
    # 各前走データのrace_keyと現在のレースのrace_keyを比較
    for col in existing_prev_cols:
        # 前走データが存在する行のみを対象
        mask = df_sample[col].notna() & (df_sample[col] != "")
        if mask.sum() == 0:
            print(f"  {col}: データなし")
            continue
        
        print(f"\n{col}の検証中...")
        prev_race_keys = df_sample.loc[mask, col].astype(str)
        current_race_keys = df_sample.loc[mask, "race_key"].astype(str)
        current_datetimes = df_sample.loc[mask, "start_datetime"]
        
        # race_keyから日付を抽出（YYYYMMDD形式を想定）
        # race_keyがYYYYMMDDHHMM形式の場合、最初の8文字が日付
        current_dates = current_race_keys.str[:8].astype(int)
        prev_dates = prev_race_keys.str[:8].astype(int)
        
        # 前走レースの日付が現在のレースの日付より後（または同じ）の場合、リーク
        leak_mask = prev_dates >= current_dates
        leak_count = leak_mask.sum()
        
        if leak_count > 0:
            invalid_count += leak_count
            leak_indices = df_sample.loc[mask][leak_mask].index[:10]  # 最初の10件を表示
            issues.append(f"{col}: {leak_count}件のリークを検出（前走レースの日付が現在のレースの日付より後または同じ）")
            print(f"  ❌ {col}: {leak_count}件のリークを検出")
            print(f"     サンプル（最初の10件）:")
            for idx in leak_indices:
                current_race_key = df_sample.loc[idx, "race_key"]
                prev_race_key = df_sample.loc[idx, col]
                current_date = str(current_race_key)[:8]
                prev_date = str(prev_race_key)[:8]
                print(f"       - インデックス: {idx}")
                print(f"         現在レース: {current_race_key} (日付: {current_date})")
                print(f"         前走レース: {prev_race_key} (日付: {prev_date})")
        else:
            valid_count += mask.sum()
            print(f"  ✅ {col}: リークなし ({mask.sum()}件)")
    
    return {
        "issues": issues,
        "warnings": warnings,
        "valid": len(issues) == 0,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
    }


def main():
    """メイン処理"""
    print("=" * 80)
    print("前走レース情報の日付検証")
    print("=" * 80)
    
    BASE_PATH = base_project_path / 'notebooks' / 'data'
    DATA_TYPES = ['BAC', 'KYI', 'SED']
    YEAR = 2024
    
    print(f"\nデータ読み込み中...")
    print(f"  データタイプ: {DATA_TYPES}")
    print(f"  年度: {YEAR}")
    
    # データ読み込み
    npz_loader = NpzLoader(BASE_PATH)
    year_data_dict = npz_loader.load(DATA_TYPES, YEAR)
    
    jrdb_combiner = JrdbCombiner(base_project_path.parent.parent)
    raw_df = jrdb_combiner.combine(year_data_dict)
    
    feature_extractor = FeatureExtractor()
    sed_df = year_data_dict.get("SED")
    bac_df = year_data_dict.get("BAC")
    if sed_df is not None:
        featured_df = feature_extractor.extract_all_parallel(raw_df, sed_df, bac_df)
    else:
        featured_df = raw_df
    
    print(f"特徴量抽出完了: {len(featured_df):,}件")
    
    # 前走レース情報の日付検証
    print("\n" + "=" * 80)
    print("前走レース情報の日付検証")
    print("=" * 80)
    
    result = check_previous_race_dates(featured_df)
    
    print("\n" + "=" * 80)
    print("検証結果")
    print("=" * 80)
    print(f"結果: {'✓ 問題なし' if result['valid'] else '✗ 問題あり'}")
    print(f"有効な前走データ: {result['valid_count']:,}件")
    print(f"無効な前走データ（リーク）: {result['invalid_count']:,}件")
    
    if result['issues']:
        print(f"\n問題: {len(result['issues'])}件")
        for issue in result['issues']:
            print(f"  - {issue}")
    
    if result['warnings']:
        print(f"\n警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    if result['valid']:
        print("\n✅ すべての前走レース情報が、現在のレース日よりも過去です。")
    else:
        print("\n❌ 前走レース情報にリークが検出されました。")
        print("   前走レースの日付が現在のレースの日付より後または同じになっています。")
    
    return 0 if result['valid'] else 1


if __name__ == "__main__":
    sys.exit(main())

