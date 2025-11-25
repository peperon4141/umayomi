"""
特徴量強化モジュール
レース内相対特徴量とインタラクション特徴量を追加
"""

from typing import List, Optional

import numpy as np
import pandas as pd


def add_relative_features(df: pd.DataFrame, race_key_col: str = "race_key") -> pd.DataFrame:
    """
    レース内での相対的な特徴量を追加
    
    Args:
        df: 対象のDataFrame（race_keyでインデックスまたはカラムとして含む）
        race_key_col: レースキーのカラム名（インデックスの場合は使用されない）
    
    Returns:
        特徴量が追加されたDataFrame
    """
    df = df.copy()
    
    # race_keyの取得方法を決定
    if df.index.name == race_key_col:
        # インデックスがrace_keyの場合
        df_with_key = df.reset_index()
        group_key = race_key_col
    elif race_key_col in df.columns:
        # race_keyがカラムの場合
        df_with_key = df.copy()
        group_key = race_key_col
    else:
        raise ValueError(f"race_key（{race_key_col}）がインデックスにもカラムにも存在しません")
    
    # レースごとにグループ化
    grouped = df_with_key.groupby(group_key)
    
    # レース内での相対的な特徴量を追加
    relative_features = [
        # 馬の統計量の順位
        ("horse_place_rate", "horse_place_rate_rank", True),  # 大きいほど良い
        ("horse_avg_rank", "horse_avg_rank_rank", False),  # 小さいほど良い
        ("horse_win_rate", "horse_win_rate_rank", True),  # 大きいほど良い
        ("horse_race_count", "horse_race_count_rank", True),  # 大きいほど良い（経験値）
        
        # 騎手の統計量の順位
        ("jockey_win_rate", "jockey_win_rate_rank", True),
        ("jockey_place_rate", "jockey_place_rate_rank", True),
        ("jockey_avg_rank", "jockey_avg_rank_rank", False),
        
        # 調教師の統計量の順位
        ("trainer_win_rate", "trainer_win_rate_rank", True),
        ("trainer_place_rate", "trainer_place_rate_rank", True),
        ("trainer_avg_rank", "trainer_avg_rank_rank", False),
        
        # 前走成績の順位
        ("prev_1_rank", "prev_1_rank_rank", False),  # 小さいほど良い
        ("prev_2_rank", "prev_2_rank_rank", False),
        ("prev_3_rank", "prev_3_rank_rank", False),
        
        # 馬体重の順位
        ("horse_weight", "horse_weight_rank", True),  # 大きいほど良い（一般的に）
        ("horse_weight_diff", "horse_weight_diff_rank", True),  # 増加している方が良い（調子が良い）
        
        # 前走タイムの順位（距離正規化後、小さいほど良い）
        ("prev_1_time", "prev_1_time_rank", False),
        ("prev_2_time", "prev_2_time_rank", False),
        
        # 指数の順位
        ("idm", "idm_rank", True),
        ("jockey_index", "jockey_index_rank", True),
        ("total_index", "total_index_rank", True),
        ("paddock_index", "paddock_index_rank", True),
        
        # 適性の順位
        ("distance_aptitude", "distance_aptitude_rank", True),
    ]
    
    for source_col, target_col, ascending in relative_features:
        if source_col in df_with_key.columns:
            # NaN値を除外してランク付け
            df_with_key[target_col] = grouped[source_col].rank(
                ascending=ascending, 
                method='min',
                na_option='keep'
            )
            # NaN値を0に置換（順位が不明な場合は最下位扱い）
            df_with_key[target_col] = df_with_key[target_col].fillna(0.0)
    
    # 元のDataFrame構造に戻す
    if df.index.name == race_key_col:
        # インデックスを復元
        result_df = df_with_key.set_index(race_key_col)
        # 元のインデックス順序を保持
        if len(result_df) == len(df):
            # 元のインデックスと一致するように並び替え
            result_df = result_df.reindex(df.index)
    else:
        result_df = df_with_key
        # 元のインデックスを保持（race_keyがカラムの場合）
        if len(result_df) == len(df):
            result_df.index = df.index
    
    return result_df


def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    インタラクション特徴量を追加（重要度上位の特徴量同士の組み合わせ）
    
    Args:
        df: 対象のDataFrame
    
    Returns:
        特徴量が追加されたDataFrame
    """
    df = df.copy()
    
    # 重要度上位の特徴量の組み合わせ
    interaction_pairs = [
        # 馬の統計量 × コースタイプ
        ("horse_place_rate", "course_type", "horse_place_rate_x_course_type"),
        ("horse_avg_rank", "course_type", "horse_avg_rank_x_course_type"),
        
        # 馬の統計量 × 距離
        ("horse_place_rate", "course_length", "horse_place_rate_x_distance"),
        ("horse_avg_rank", "course_length", "horse_avg_rank_x_distance"),
        ("distance_aptitude", "course_length", "distance_aptitude_x_course_length"),
        
        # 枠番 × 頭数
        ("frame", "num_horses", "frame_x_num_horses"),
        
        # 前走成績 × コースタイプ
        ("prev_1_rank", "prev_1_course_type", "prev_1_rank_x_course_type"),
        ("prev_1_course_type", "course_type", "prev_1_course_type_x_current_course_type"),
        ("prev_2_course_type", "course_type", "prev_2_course_type_x_current_course_type"),
        
        # 前走成績 × 距離
        ("prev_1_rank", "prev_1_distance", "prev_1_rank_x_distance"),
        ("prev_1_distance", "course_length", "prev_1_distance_x_current_distance"),
        ("prev_2_distance", "course_length", "prev_2_distance_x_current_distance"),
        
        # 騎手 × 調教師
        ("jockey_win_rate", "trainer_win_rate", "jockey_win_rate_x_trainer_win_rate"),
        ("jockey_place_rate", "trainer_place_rate", "jockey_place_rate_x_trainer_place_rate"),
        
        # 馬体重 × 距離
        ("horse_weight", "course_length", "horse_weight_x_distance"),
        ("horse_weight_diff", "course_length", "horse_weight_diff_x_distance"),
        
        # 前走成績 × 馬場状態
        ("prev_1_rank", "prev_1_ground_condition", "prev_1_rank_x_ground_condition"),
        ("prev_1_ground_condition", "ground_condition", "prev_1_ground_condition_x_current_ground_condition"),
        
        # 年齢 × 距離
        ("age", "course_length", "age_x_distance"),
        
        # 前走頭数 × 現在頭数
        ("prev_1_num_horses", "num_horses", "prev_1_num_horses_x_current_num_horses"),
        ("prev_2_num_horses", "num_horses", "prev_2_num_horses_x_current_num_horses"),
    ]
    
    for col1, col2, target_col in interaction_pairs:
        if col1 in df.columns and col2 in df.columns:
            # 数値型の場合は乗算、カテゴリカル型の場合は文字列結合
            if df[col1].dtype in [np.int64, np.int32, np.float64, np.float32] and \
               df[col2].dtype in [np.int64, np.int32, np.float64, np.float32]:
                # 数値型同士の場合は乗算
                df[target_col] = df[col1] * df[col2]
            else:
                # カテゴリカル型が含まれる場合は、数値型に変換してから乗算
                # または、カテゴリカル型を数値化（Label Encoding的な処理）
                col1_numeric = pd.to_numeric(df[col1], errors='coerce')
                col2_numeric = pd.to_numeric(df[col2], errors='coerce')
                
                if col1_numeric.notna().all() and col2_numeric.notna().all():
                    # 両方とも数値化可能な場合
                    df[target_col] = col1_numeric * col2_numeric
                else:
                    # カテゴリカル型を含む場合は、カテゴリカル型を数値化
                    # 文字列の場合はハッシュ値を使用（簡易的なエンコーディング）
                    if df[col1].dtype == 'object':
                        col1_encoded = df[col1].astype(str).apply(lambda x: hash(x) % 1000)
                    else:
                        col1_encoded = pd.to_numeric(df[col1], errors='coerce').fillna(0)
                    
                    if df[col2].dtype == 'object':
                        col2_encoded = df[col2].astype(str).apply(lambda x: hash(x) % 1000)
                    else:
                        col2_encoded = pd.to_numeric(df[col2], errors='coerce').fillna(0)
                    
                    df[target_col] = col1_encoded * col2_encoded
    
    return df


def enhance_features(df: pd.DataFrame, race_key_col: str = "race_key") -> pd.DataFrame:
    """
    特徴量を強化（レース内相対特徴量とインタラクション特徴量を追加）
    
    Args:
        df: 対象のDataFrame
        race_key_col: レースキーのカラム名
    
    Returns:
        特徴量が追加されたDataFrame
    """
    print("特徴量強化を開始します...")
    print(f"  元の特徴量数: {len(df.columns)}")
    
    # レース内相対特徴量を追加
    print("  レース内相対特徴量を追加中...")
    df = add_relative_features(df, race_key_col)
    print(f"  レース内相対特徴量追加後: {len(df.columns)}")
    
    # インタラクション特徴量を追加
    print("  インタラクション特徴量を追加中...")
    df = add_interaction_features(df)
    print(f"  特徴量強化完了: {len(df.columns)}")
    
    return df

