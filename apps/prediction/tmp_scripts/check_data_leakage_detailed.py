"""
詳細なデータリークチェック

1. 前走データのリーク（converted_dfで確認）
2. 統計特徴量のリーク（時系列フィルタリングの確認）
3. 時系列分割のリーク
4. 平均順位誤差が異常に大きい原因の調査
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

from src.data_processer.npz_loader import NpzLoader
from src.data_processer.jrdb_combiner import JrdbCombiner
from src.data_processer.feature_extractor import FeatureExtractor
from src.data_processer.key_converter import KeyConverter
from src.data_processer.time_series_splitter import TimeSeriesSplitter
from src.data_processer.column_selector import ColumnSelector


def check_previous_race_leakage_detailed(df: pd.DataFrame) -> dict:
    """
    前走データのリークを詳細にチェック
    
    featured_df（日本語キー）で確認
    """
    issues = []
    warnings = []
    
    # race_keyをカラムとして取得
    if df.index.name == "race_key":
        df_check = df.reset_index()
    elif "race_key" not in df.columns:
        return {"issues": ["race_keyカラムが見つかりません"], "warnings": [], "valid": False}
    else:
        df_check = df.copy()
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in df_check.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False}
    
    # 前走データのrace_keyカラムを確認
    prev_race_key_cols = [f"prev_{i}_race_key" for i in range(1, 6)]
    existing_prev_cols = [col for col in prev_race_key_cols if col in df_check.columns]
    
    if not existing_prev_cols:
        warnings.append("前走データのrace_keyカラムが見つかりません（データ変換時に削除された可能性）")
        # 前走データの他のカラムで確認
        prev_rank_cols = [f"prev_{i}_rank" for i in range(1, 6)]
        existing_prev_rank_cols = [col for col in prev_rank_cols if col in df_check.columns]
        if existing_prev_rank_cols:
            warnings.append(f"前走データのrankカラムは存在します: {existing_prev_rank_cols}")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}
    
    print(f"検証対象カラム: {existing_prev_cols}")
    
    # サンプルサイズを制限（メモリ使用量削減）
    sample_size = min(10000, len(df_check))
    df_sample = df_check.sample(n=sample_size, random_state=42) if len(df_check) > sample_size else df_check
    
    leak_count = 0
    for col in existing_prev_cols:
        # 前走データが存在する行のみを対象
        mask = df_sample[col].notna() & (df_sample[col] != "")
        if mask.sum() == 0:
            continue
        
        # 前走race_keyと現在のrace_keyを比較
        prev_race_keys = df_sample.loc[mask, col].astype(str)
        current_race_keys = df_sample.loc[mask, "race_key"].astype(str)
        current_datetimes = df_sample.loc[mask, "start_datetime"]
        
        # 前走レースのstart_datetimeを取得
        for idx in df_sample.loc[mask].index[:1000]:  # 最大1000件チェック
            prev_race_key = str(df_sample.loc[idx, col])
            current_race_key = str(df_sample.loc[idx, "race_key"])
            current_datetime = df_sample.loc[idx, "start_datetime"]
            
            # 前走レースのデータを取得
            prev_race_row = df_check[df_check["race_key"] == prev_race_key]
            
            if len(prev_race_row) == 0:
                continue
            
            prev_datetime = prev_race_row.iloc[0]["start_datetime"]
            
            if pd.isna(prev_datetime) or pd.isna(current_datetime):
                continue
            
            # 前走レースの日時が現在のレースより後でないか確認
            if prev_datetime > current_datetime:
                leak_count += 1
                if leak_count <= 10:  # 最初の10件のみ表示
                    issues.append(
                        f"リーク検出: race_key={current_race_key}, "
                        f"前走race_key={prev_race_key}, "
                        f"現在日時={current_datetime}, 前走日時={prev_datetime}"
                    )
                if leak_count >= 100:  # 100件検出したら停止
                    issues.append(f"... 他{leak_count - 10}件のリークを検出")
                    break
        
        if leak_count >= 100:
            break
    
    if leak_count > 0:
        issues.insert(0, f"前走データのリーク: 合計{leak_count}件検出")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def check_statistics_leakage_detailed(df: pd.DataFrame) -> dict:
    """
    統計特徴量のリークを詳細にチェック
    
    時系列的に統計量が増加することを確認
    """
    issues = []
    warnings = []
    
    # race_keyをカラムとして取得
    if df.index.name == "race_key":
        df_check = df.reset_index()
    elif "race_key" not in df.columns:
        return {"issues": ["race_keyカラムが見つかりません"], "warnings": [], "valid": False}
    else:
        df_check = df.copy()
    
    # start_datetimeが存在するか確認
    if "start_datetime" not in df_check.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False}
    
    # 統計特徴量のカラムを確認
    stats_cols = [col for col in df_check.columns if any(
        keyword in col for keyword in ["勝率", "連対率", "平均着順", "出走回数", "win_rate", "place_rate", "avg_rank", "race_count"]
    )]
    
    if not stats_cols:
        warnings.append("統計特徴量のカラムが見つかりません")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}
    
    print(f"検証対象カラム: {stats_cols[:10]}...")  # 最初の10個のみ表示
    
    # 時系列順にソート
    df_sorted = df_check.sort_values("start_datetime").reset_index(drop=True)
    
    # 累積値（cumsum, cumcount, race_count）が時系列的に増加することを確認
    cumulative_cols = [col for col in stats_cols if "cumsum" in col or "cumcount" in col or "race_count" in col]
    
    for col in cumulative_cols[:5]:  # 最初の5つの累積値カラムのみチェック
        if df_sorted[col].dtype not in [np.float64, np.int64, np.float32, np.int32]:
            continue
        
        # 同じ馬/騎手/調教師でグループ化
        group_cols = []
        for group_col in ["血統登録番号", "騎手コード", "調教師コード", "horse_id", "jockey_id", "trainer_id"]:
            if group_col in df_sorted.columns:
                group_cols.append(group_col)
                break  # 最初に見つかったグループカラムを使用
        
        if not group_cols:
            continue
        
        # サンプルグループを取得
        sample_groups = df_sorted.groupby(group_cols).size()
        sample_groups = sample_groups[sample_groups >= 3].head(20)  # 20グループのみ
        
        for group_key, group_df in df_sorted.groupby(group_cols):
            if group_key not in sample_groups.index:
                continue
            
            group_sorted = group_df.sort_values("start_datetime")
            values = group_sorted[col].values
            
            # 累積値は時系列的に増加するはず
            if len(values) > 1:
                decreases = np.sum(values[1:] < values[:-1])
                if decreases > 0:
                    issues.append(
                        f"統計特徴量のリーク可能性: {col}, "
                        f"グループ={group_key}, "
                        f"時系列的に減少している値が{decreases}件存在"
                    )
                    if len(issues) >= 10:
                        break
        
        if len(issues) >= 10:
            break
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def check_mean_rank_error(df: pd.DataFrame) -> dict:
    """
    平均順位誤差が異常に大きい原因を調査
    """
    issues = []
    warnings = []
    
    # rank列が存在するか確認
    if "rank" not in df.columns:
        return {"issues": ["rankカラムが見つかりません"], "warnings": [], "valid": False}
    
    # rank列の統計を確認
    rank_stats = df["rank"].describe()
    print(f"\nrank列の統計:")
    print(f"  平均: {rank_stats['mean']:.2f}")
    print(f"  中央値: {rank_stats['50%']:.2f}")
    print(f"  最小値: {rank_stats['min']:.2f}")
    print(f"  最大値: {rank_stats['max']:.2f}")
    print(f"  標準偏差: {rank_stats['std']:.2f}")
    
    # 異常値の確認
    if rank_stats['max'] > 100:
        warnings.append(f"rank列の最大値が異常に大きい: {rank_stats['max']:.2f}")
    
    # NaN値の確認
    nan_count = df["rank"].isna().sum()
    if nan_count > 0:
        warnings.append(f"rank列にNaN値が{nan_count}件存在")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def main():
    """メイン処理"""
    print("=" * 80)
    print("詳細なデータリークチェック")
    print("=" * 80)
    
    BASE_PATH = base_project_path / 'notebooks' / 'data'
    DATA_TYPES = ['BAC', 'KYI', 'SED']
    YEARS = [2023, 2024]
    split_date = "2024-06-01"
    
    print(f"\nデータ読み込み中...")
    print(f"  データタイプ: {DATA_TYPES}")
    print(f"  年度: {YEARS}")
    print(f"  分割日時: {split_date}")
    
    # 年度ごとに分割して処理
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
            del raw_df, sed_df
            if bac_df is not None:
                del bac_df
        else:
            featured_df = raw_df
        del year_data_dict
        
        import gc
        gc.collect()
        
        featured_dfs.append(featured_df)
        print(f"{year}年の特徴量抽出完了: {len(featured_df):,}件")
    
    # 年度ごとの特徴量抽出結果を結合
    featured_df = pd.concat(featured_dfs, ignore_index=True)
    del featured_dfs
    import gc
    gc.collect()
    print(f"\n結合完了: {len(featured_df):,}件")
    
    # featured_dfで前走データのリークをチェック（日本語キー）
    print("\n" + "=" * 80)
    print("1. featured_df（日本語キー）での前走データリークチェック")
    print("=" * 80)
    featured_prev_result = check_previous_race_leakage_detailed(featured_df)
    print(f"結果: {'✓ 問題なし' if featured_prev_result['valid'] else '✗ 問題あり'}")
    if featured_prev_result['issues']:
        print(f"問題: {len(featured_prev_result['issues'])}件")
        for issue in featured_prev_result['issues'][:10]:
            print(f"  - {issue}")
    if featured_prev_result['warnings']:
        for warning in featured_prev_result['warnings']:
            print(f"  警告: {warning}")
    
    # featured_dfで統計特徴量のリークをチェック
    print("\n" + "=" * 80)
    print("2. featured_df（日本語キー）での統計特徴量リークチェック")
    print("=" * 80)
    featured_stats_result = check_statistics_leakage_detailed(featured_df)
    print(f"結果: {'✓ 問題なし' if featured_stats_result['valid'] else '✗ 問題あり'}")
    if featured_stats_result['issues']:
        print(f"問題: {len(featured_stats_result['issues'])}件")
        for issue in featured_stats_result['issues'][:10]:
            print(f"  - {issue}")
    if featured_stats_result['warnings']:
        for warning in featured_stats_result['warnings']:
            print(f"  警告: {warning}")
    
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
    time_series_splitter = TimeSeriesSplitter()
    train_df, test_df = time_series_splitter.split(converted_df, split_date)
    
    # カラム選択
    column_selector = ColumnSelector(base_project_path.parent.parent)
    train_df = column_selector.select_training(train_df)
    test_df = column_selector.select_training(test_df)
    
    print(f"\nデータ読み込み完了:")
    print(f"  学習データ: {len(train_df):,}件")
    print(f"  テストデータ: {len(test_df):,}件")
    
    # converted_dfで前走データのリークをチェック（英語キー）
    print("\n" + "=" * 80)
    print("3. converted_df（英語キー）での前走データリークチェック")
    print("=" * 80)
    # converted_dfをリセットしてrace_keyをカラムとして取得
    converted_df_check = converted_df.reset_index()
    converted_prev_result = check_previous_race_leakage_detailed(converted_df_check)
    print(f"結果: {'✓ 問題なし' if converted_prev_result['valid'] else '✗ 問題あり'}")
    if converted_prev_result['issues']:
        print(f"問題: {len(converted_prev_result['issues'])}件")
        for issue in converted_prev_result['issues'][:10]:
            print(f"  - {issue}")
    if converted_prev_result['warnings']:
        for warning in converted_prev_result['warnings']:
            print(f"  警告: {warning}")
    
    # 時系列分割のリークチェック
    print("\n" + "=" * 80)
    print("4. 時系列分割のリークチェック")
    print("=" * 80)
    from tmp_scripts.check_data_leakage import check_train_test_split
    split_result = check_train_test_split(train_df, test_df, split_date)
    print(f"結果: {'✓ 問題なし' if split_result['valid'] else '✗ 問題あり'}")
    if split_result['issues']:
        print(f"問題: {len(split_result['issues'])}件")
        for issue in split_result['issues']:
            print(f"  - {issue}")
    
    # 平均順位誤差の調査
    print("\n" + "=" * 80)
    print("5. 平均順位誤差が異常に大きい原因の調査")
    print("=" * 80)
    rank_error_result = check_mean_rank_error(test_df)
    if rank_error_result['warnings']:
        for warning in rank_error_result['warnings']:
            print(f"  警告: {warning}")
    
    # 結果をまとめる
    print("\n" + "=" * 80)
    print("【検証結果サマリー】")
    print("=" * 80)
    
    all_issues = []
    all_warnings = []
    
    results = {
        "featured_previous_race": featured_prev_result,
        "featured_statistics": featured_stats_result,
        "converted_previous_race": converted_prev_result,
        "train_test_split": split_result,
    }
    
    for check_name, result in results.items():
        if result.get("issues"):
            all_issues.extend([f"{check_name}: {issue}" for issue in result["issues"]])
        if result.get("warnings"):
            all_warnings.extend([f"{check_name}: {warning}" for warning in result["warnings"]])
    
    if all_issues:
        print("\n❌ 検出された問題:")
        for issue in all_issues[:20]:  # 最初の20件のみ表示
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


if __name__ == "__main__":
    sys.exit(main())

