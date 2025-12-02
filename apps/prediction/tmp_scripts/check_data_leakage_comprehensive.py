"""
包括的なデータリークチェック

以下の項目をチェック：
1. 前走データのリーク（未来のレースのデータが使用されていないか）
2. 統計特徴量のリーク（未来のレースのデータが統計計算に含まれていないか）
3. 時系列分割のリーク（テストデータが学習データより前の日付でないか）
4. start_datetimeの整合性
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

# プロジェクトルートをパスに追加
base_project_path = Path(__file__).parent.parent
sys.path.insert(0, str(base_project_path))

from src.data_processer.npz_loader import NpzLoader
from src.data_processer.jrdb_combiner import JrdbCombiner
from src.data_processer.feature_extractor import FeatureExtractor
from src.data_processer.key_converter import KeyConverter
from src.data_processer.time_series_splitter import TimeSeriesSplitter
from src.data_processer.column_selector import ColumnSelector


def check_previous_race_leakage(df: pd.DataFrame) -> dict:
    """
    前走データのリークをチェック
    
    各レースの前走データが、そのレースより未来のレースのデータを含んでいないか確認
    """
    issues = []
    warnings = []
    
    if "race_key" not in df.columns and df.index.name != "race_key":
        return {"issues": ["race_keyカラムまたはインデックスが見つかりません"], "warnings": [], "valid": False}
    
    # race_keyをカラムとして取得
    if df.index.name == "race_key":
        df_check = df.reset_index()
    else:
        df_check = df.copy()
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in df_check.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False}
    
    # 前走データのカラムを取得
    prev_cols = [col for col in df_check.columns if col.startswith("prev_") and "race_key" in col]
    
    if not prev_cols:
        warnings.append("前走データのrace_keyカラムが見つかりません（前走データが存在しない可能性）")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}
    
    # 各レースの前走データをチェック
    sample_size = min(1000, len(df_check))  # サンプルサイズを制限
    df_sample = df_check.sample(n=sample_size, random_state=42) if len(df_check) > sample_size else df_check
    
    for idx, row in df_sample.iterrows():
        current_race_key = str(row["race_key"])
        current_datetime = row["start_datetime"]
        
        if pd.isna(current_datetime):
            continue
        
        # 前走データのrace_keyをチェック
        for prev_col in prev_cols:
            prev_race_key = row[prev_col]
            
            if pd.isna(prev_race_key) or prev_race_key == "":
                continue
            
            prev_race_key = str(prev_race_key)
            
            # 前走レースのstart_datetimeを取得
            prev_race_row = df_check[df_check["race_key"] == prev_race_key]
            
            if len(prev_race_row) == 0:
                continue
            
            prev_datetime = prev_race_row.iloc[0]["start_datetime"]
            
            if pd.isna(prev_datetime):
                continue
            
            # 前走レースの日時が現在のレースより後でないか確認
            if prev_datetime > current_datetime:
                issues.append(
                    f"リーク検出: race_key={current_race_key}, "
                    f"前走race_key={prev_race_key}, "
                    f"現在日時={current_datetime}, 前走日時={prev_datetime}"
                )
                if len(issues) >= 10:  # 最大10件まで
                    break
        
        if len(issues) >= 10:
            break
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def check_statistics_leakage(df: pd.DataFrame) -> dict:
    """
    統計特徴量のリークをチェック
    
    各レースの統計特徴量が、そのレースより未来のレースのデータを含んでいないか確認
    """
    issues = []
    warnings = []
    
    if "race_key" not in df.columns and df.index.name != "race_key":
        return {"issues": ["race_keyカラムまたはインデックスが見つかりません"], "warnings": [], "valid": False}
    
    # race_keyをカラムとして取得
    if df.index.name == "race_key":
        df_check = df.reset_index()
    else:
        df_check = df.copy()
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in df_check.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False}
    
    # 統計特徴量のカラムを取得（勝率、連対率、平均着順など）
    stats_cols = [col for col in df_check.columns if any(
        keyword in col for keyword in ["勝率", "連対率", "平均着順", "出走回数", "cumsum", "cumcount"]
    )]
    
    if not stats_cols:
        warnings.append("統計特徴量のカラムが見つかりません")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}
    
    # 時系列順にソート
    df_sorted = df_check.sort_values("start_datetime").reset_index(drop=True)
    
    # 各統計特徴量について、時系列的に増加することを確認（未来情報が含まれていない場合）
    # ただし、これは簡易チェックであり、完全な検証ではない
    
    for col in stats_cols[:5]:  # 最初の5つの統計特徴量のみチェック
        if df_sorted[col].dtype not in [np.float64, np.int64, np.float32, np.int32]:
            continue
        
        # 同じ馬/騎手/調教師でグループ化して、時系列的に増加することを確認
        group_cols = []
        for group_col in ["血統登録番号", "騎手コード", "調教師コード"]:
            if group_col in df_sorted.columns:
                group_cols.append(group_col)
        
        if not group_cols:
            continue
        
        # サンプルサイズを制限
        sample_groups = df_sorted.groupby(group_cols).size()
        sample_groups = sample_groups[sample_groups >= 3].head(10)  # 10グループのみ
        
        for group_key, group_df in df_sorted.groupby(group_cols):
            if group_key not in sample_groups.index:
                continue
            
            group_sorted = group_df.sort_values("start_datetime")
            values = group_sorted[col].values
            
            # 累積値（cumsum, cumcount）は時系列的に増加するはず
            if "cumsum" in col or "cumcount" in col:
                if not np.all(values[1:] >= values[:-1]):
                    issues.append(
                        f"統計特徴量のリーク可能性: {col}, "
                        f"グループ={group_key}, 時系列的に減少している値が存在"
                    )
                    if len(issues) >= 5:
                        break
        
        if len(issues) >= 5:
            break
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def check_train_test_split(train_df: pd.DataFrame, test_df: pd.DataFrame, split_date: str) -> dict:
    """
    時系列分割のリークをチェック
    
    テストデータが学習データより前の日付でないか確認
    """
    issues = []
    warnings = []
    
    # race_keyをカラムとして取得
    if train_df.index.name == "race_key":
        train_check = train_df.reset_index()
    else:
        train_check = train_df.copy()
    
    if test_df.index.name == "race_key":
        test_check = test_df.reset_index()
    else:
        test_check = test_df.copy()
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in train_check.columns or "start_datetime" not in test_check.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False}
    
    # 分割日時を取得
    split_datetime = pd.to_datetime(split_date)
    
    # 学習データの最大日時
    train_max_datetime = train_check["start_datetime"].max()
    
    # テストデータの最小日時
    test_min_datetime = test_check["start_datetime"].min()
    
    # 学習データに分割日時より後のデータが含まれていないか確認
    train_after_split = train_check[train_check["start_datetime"] > split_datetime]
    if len(train_after_split) > 0:
        issues.append(
            f"学習データに分割日時({split_date})より後のデータが含まれています: "
            f"{len(train_after_split)}件"
        )
    
    # テストデータに分割日時より前のデータが含まれていないか確認
    test_before_split = test_check[test_check["start_datetime"] <= split_datetime]
    if len(test_before_split) > 0:
        issues.append(
            f"テストデータに分割日時({split_date})より前のデータが含まれています: "
            f"{len(test_before_split)}件"
        )
    
    # テストデータの最小日時が学習データの最大日時より前でないか確認
    if test_min_datetime < train_max_datetime:
        issues.append(
            f"テストデータの最小日時({test_min_datetime})が学習データの最大日時({train_max_datetime})より前です"
        )
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def main():
    """メイン処理"""
    print("=" * 80)
    print("データリークチェック開始")
    print("=" * 80)
    
    BASE_PATH = base_project_path.parent.parent / "notebooks" / "data"
    DATA_TYPES = ["BAC", "KYI", "SED"]
    YEARS = [2023, 2024]
    split_date = "2024-06-01"
    
    # データ読み込み
    print("\nデータ読み込み中...")
    featured_dfs = []
    for year in YEARS:
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
    
    featured_df = pd.concat(featured_dfs, ignore_index=True)
    print(f"データ読み込み完了: {len(featured_df):,}件")
    
    # データ変換
    print("\nデータ変換中...")
    key_converter = KeyConverter(base_project_path.parent.parent)
    converted_df = key_converter.convert(featured_df)
    converted_df = key_converter.optimize(converted_df)
    
    # インデックス設定
    if "race_key" in converted_df.columns:
        converted_df.set_index("race_key", inplace=True)
        if "start_datetime" in converted_df.columns:
            converted_df = converted_df.sort_values("start_datetime", ascending=True)
    
    # 時系列分割
    print("\n時系列分割中...")
    time_series_splitter = TimeSeriesSplitter()
    train_df, test_df = time_series_splitter.split(converted_df, split_date)
    
    # カラム選択
    column_selector = ColumnSelector(base_project_path.parent.parent)
    train_df = column_selector.select_training(train_df)
    test_df = column_selector.select_training(test_df)
    
    print(f"学習データ: {len(train_df):,}件")
    print(f"テストデータ: {len(test_df):,}件")
    
    # リークチェック実行
    print("\n" + "=" * 80)
    print("1. 前走データのリークチェック")
    print("=" * 80)
    prev_race_result = check_previous_race_leakage(converted_df)
    print(f"結果: {'✓ 問題なし' if prev_race_result['valid'] else '✗ 問題あり'}")
    if prev_race_result['issues']:
        print(f"問題: {len(prev_race_result['issues'])}件")
        for issue in prev_race_result['issues'][:5]:
            print(f"  - {issue}")
    if prev_race_result['warnings']:
        for warning in prev_race_result['warnings']:
            print(f"  警告: {warning}")
    
    print("\n" + "=" * 80)
    print("2. 統計特徴量のリークチェック")
    print("=" * 80)
    stats_result = check_statistics_leakage(converted_df)
    print(f"結果: {'✓ 問題なし' if stats_result['valid'] else '✗ 問題あり'}")
    if stats_result['issues']:
        print(f"問題: {len(stats_result['issues'])}件")
        for issue in stats_result['issues'][:5]:
            print(f"  - {issue}")
    if stats_result['warnings']:
        for warning in stats_result['warnings']:
            print(f"  警告: {warning}")
    
    print("\n" + "=" * 80)
    print("3. 時系列分割のリークチェック")
    print("=" * 80)
    split_result = check_train_test_split(train_df, test_df, split_date)
    print(f"結果: {'✓ 問題なし' if split_result['valid'] else '✗ 問題あり'}")
    if split_result['issues']:
        print(f"問題: {len(split_result['issues'])}件")
        for issue in split_result['issues']:
            print(f"  - {issue}")
    if split_result['warnings']:
        for warning in split_result['warnings']:
            print(f"  警告: {warning}")
    
    # 総合結果
    print("\n" + "=" * 80)
    print("総合結果")
    print("=" * 80)
    all_valid = prev_race_result['valid'] and stats_result['valid'] and split_result['valid']
    print(f"データリークチェック: {'✓ 問題なし' if all_valid else '✗ 問題あり'}")
    
    if not all_valid:
        print("\n注意: データリークが検出されました。モデルの的中率が異常に高い原因の可能性があります。")
    else:
        print("\nデータリークは検出されませんでした。")


if __name__ == "__main__":
    main()

