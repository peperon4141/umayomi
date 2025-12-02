"""
統計特徴量のリークを詳細にチェック

統計特徴量の計算時に、現在のレースが含まれていないか確認
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
from src.data_processer.feature_converter import FeatureConverter


def check_statistics_leakage_detailed(df: pd.DataFrame) -> dict:
    """
    統計特徴量のリークを詳細にチェック
    
    各レースの統計特徴量が、そのレース自身を含んでいないか確認
    """
    issues = []
    warnings = []
    
    # race_keyとstart_datetimeが存在するか確認
    if "race_key" not in df.columns:
        return {"issues": ["race_keyカラムが見つかりません"], "warnings": [], "valid": False}
    
    if "start_datetime" not in df.columns:
        return {"issues": ["start_datetimeカラムが見つかりません"], "warnings": [], "valid": False}
    
    # 統計特徴量のカラムを確認
    stats_cols = [col for col in df.columns if any(
        keyword in col for keyword in ["勝率", "連対率", "平均着順", "出走回数", "win_rate", "place_rate", "avg_rank", "race_count"]
    )]
    
    if not stats_cols:
        warnings.append("統計特徴量のカラムが見つかりません")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}
    
    print(f"検証対象カラム: {stats_cols[:10]}...")
    
    # サンプルサイズを制限
    sample_size = min(5000, len(df))
    df_sample = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
    
    print(f"サンプルサイズ: {len(df_sample):,}件")
    
    # 同じ馬/騎手/調教師でグループ化して、時系列的に増加することを確認
    group_cols = []
    for group_col in ["血統登録番号", "騎手コード", "調教師コード"]:
        if group_col in df_sample.columns:
            group_cols.append(group_col)
            break  # 最初に見つかったグループカラムを使用
    
    if not group_cols:
        warnings.append("グループカラム（血統登録番号、騎手コード、調教師コード）が見つかりません")
        return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}
    
    group_col = group_cols[0]
    print(f"グループカラム: {group_col}")
    
    # 時系列順にソート
    df_sorted = df_sample.sort_values("start_datetime").reset_index(drop=True)
    
    # 累積値（cumsum, cumcount, race_count）が時系列的に増加することを確認
    cumulative_cols = [col for col in stats_cols if "cumsum" in col or "cumcount" in col or "race_count" in col or "出走回数" in col]
    
    leak_count = 0
    for col in cumulative_cols[:5]:  # 最初の5つの累積値カラムのみチェック
        if df_sorted[col].dtype not in [np.float64, np.int64, np.float32, np.int32]:
            continue
        
        # サンプルグループを取得
        sample_groups = df_sorted.groupby(group_col).size()
        sample_groups = sample_groups[sample_groups >= 3].head(50)  # 50グループのみ
        
        for group_key, group_df in df_sorted.groupby(group_col):
            if group_key not in sample_groups.index:
                continue
            
            group_sorted = group_df.sort_values("start_datetime")
            values = group_sorted[col].values
            race_keys = group_sorted["race_key"].values
            datetimes = group_sorted["start_datetime"].values
            
            # 累積値は時系列的に増加するはず
            if len(values) > 1:
                decreases = np.sum(values[1:] < values[:-1])
                if decreases > 0:
                    leak_count += 1
                    if leak_count <= 10:  # 最初の10件のみ表示
                        decrease_indices = np.where(values[1:] < values[:-1])[0]
                        for idx in decrease_indices[:3]:  # 最初の3件のみ表示
                            issues.append(
                                f"統計特徴量のリーク可能性: {col}, "
                                f"グループ={group_key}, "
                                f"race_key={race_keys[idx+1]}, "
                                f"時系列的に減少している値が存在 "
                                f"({values[idx]} -> {values[idx+1]})"
                            )
                    if leak_count >= 100:  # 100件検出したら停止
                        issues.append(f"... 他{leak_count - 10}件のリークを検出")
                        break
        
        if leak_count >= 100:
            break
    
    if leak_count > 0:
        issues.insert(0, f"統計特徴量のリーク: 合計{leak_count}件検出")
    
    # 同じレースが統計計算に含まれているか確認
    # これは、stats_dfに現在のレースが含まれている可能性をチェック
    print("\n同じレースが統計計算に含まれているか確認中...")
    same_race_count = 0
    
    # サンプルレースを取得
    sample_races = df_sample["race_key"].unique()[:100]
    
    for race_key in sample_races:
        race_data = df_sample[df_sample["race_key"] == race_key]
        if len(race_data) == 0:
            continue
        
        # 同じレース内で、同じ馬/騎手/調教師の統計量が異なるか確認
        # 統計量は同じレース内で同じ値であるべき（同じ過去データから計算されるため）
        for group_col in ["血統登録番号", "騎手コード", "調教師コード"]:
            if group_col not in race_data.columns:
                continue
            
            for stat_col in stats_cols[:3]:  # 最初の3つの統計量のみチェック
                if stat_col not in race_data.columns:
                    continue
                
                # 同じグループ内で統計量が異なる場合、問題の可能性
                grouped = race_data.groupby(group_col)[stat_col]
                if grouped.nunique().max() > 1:
                    same_race_count += 1
                    if same_race_count <= 10:  # 最初の10件のみ表示
                        issues.append(
                            f"同じレース内で統計量が異なる: {stat_col}, "
                            f"race_key={race_key}, "
                            f"グループ={group_col}, "
                            f"異なる値の数={grouped.nunique().max()}"
                        )
                    if same_race_count >= 100:
                        break
            
            if same_race_count >= 100:
                break
        
        if same_race_count >= 100:
            break
    
    if same_race_count > 0:
        issues.insert(0, f"同じレースが統計計算に含まれている可能性: {same_race_count}件検出")
    
    return {"issues": issues, "warnings": warnings, "valid": len(issues) == 0}


def main():
    """メイン処理"""
    print("=" * 80)
    print("統計特徴量のリーク詳細チェック")
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
    
    # 統計特徴量のリークチェック
    print("\n" + "=" * 80)
    print("統計特徴量のリーク詳細チェック")
    print("=" * 80)
    
    result = check_statistics_leakage_detailed(featured_df)
    
    print("\n" + "=" * 80)
    print("検証結果")
    print("=" * 80)
    print(f"結果: {'✓ 問題なし' if result['valid'] else '✗ 問題あり'}")
    
    if result['issues']:
        print(f"\n問題: {len(result['issues'])}件")
        for issue in result['issues'][:20]:  # 最初の20件のみ表示
            print(f"  - {issue}")
        if len(result['issues']) > 20:
            print(f"  ... 他{len(result['issues']) - 20}件")
    
    if result['warnings']:
        print(f"\n警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")
    
    if result['valid']:
        print("\n✅ 統計特徴量にリークは検出されませんでした。")
    else:
        print("\n❌ 統計特徴量にリークが検出されました。")
        print("   現在のレースが統計計算に含まれている可能性があります。")
    
    return 0 if result['valid'] else 1


if __name__ == "__main__":
    sys.exit(main())

