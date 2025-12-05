#!/usr/bin/env python3
"""WIN5フラグと評価結果の妥当性を確認するスクリプト"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data_processer import DataProcessor

base_project_path = Path(__file__).resolve().parent.parent
data_processor = DataProcessor()

DATA_TYPES = ['BAC', 'KYI', 'SED', 'UKC', 'TYB']
YEAR = 2024
SPLIT_DATE = '2024-06-01'

train_df, test_df, eval_df = data_processor.process(
    year=YEAR,
    split_date=SPLIT_DATE,
)

print('=' * 80)
print('評価用データのWIN5フラグの確認')
print('=' * 80)

eval_df_check = eval_df.reset_index() if eval_df.index.name == 'race_key' else eval_df.copy()

if 'WIN5フラグ' in eval_df_check.columns:
    print(f'WIN5フラグカラムが存在します')
    print(f'  総データ数: {len(eval_df_check):,}件')
    print(f'  WIN5フラグが存在する行数: {eval_df_check["WIN5フラグ"].notna().sum():,}件')
    print()
    print(f'  WIN5フラグの値の分布（最初の20件）:')
    win5_counts = eval_df_check['WIN5フラグ'].value_counts().head(20)
    print(win5_counts)
    print()
    print(f'  WIN5フラグのデータ型: {eval_df_check["WIN5フラグ"].dtype}')
    print(f'  WIN5フラグのサンプル値（最初の20件）:')
    print(eval_df_check['WIN5フラグ'].head(20).tolist())
    print()
    
    # 空文字列やNaNを除外して数値に変換
    win5_numeric = pd.to_numeric(eval_df_check['WIN5フラグ'], errors='coerce')
    print(f'  数値に変換可能なWIN5フラグの行数: {win5_numeric.notna().sum():,}件')
    print(f'  数値に変換可能なWIN5フラグの値の分布:')
    win5_numeric_counts = win5_numeric.value_counts().sort_index()
    print(win5_numeric_counts)
    print()
    print(f'  WIN5フラグ1～5の値を持つ行数:')
    for i in range(1, 6):
        count = (win5_numeric == i).sum()
        print(f'    WIN5フラグ={i}: {count:,}件')
    print()
    
    # 日付ごとのWIN5フラグ1～5の分布
    if 'race_key' in eval_df_check.columns:
        eval_df_check['date'] = eval_df_check['race_key'].astype(str).str[:8]
        print(f'  日付ごとのWIN5フラグ1～5の分布:')
        date_win5_stats = []
        for date in sorted(eval_df_check['date'].unique()):
            date_data = eval_df_check[eval_df_check['date'] == date]
            win5_flags_raw = date_data['WIN5フラグ']
            win5_flags = pd.to_numeric(win5_flags_raw, errors='coerce').dropna().astype(int)
            if len(win5_flags) > 0:
                unique_flags = sorted(win5_flags.unique())
                has_all_flags = set(unique_flags) >= {1, 2, 3, 4, 5}
                date_win5_stats.append({
                    'date': date,
                    'race_count': len(date_data),
                    'win5_flags': unique_flags,
                    'has_all_flags': has_all_flags
                })
        
        # WIN5フラグ1～5が揃った日を表示
        complete_days = [s for s in date_win5_stats if s['has_all_flags']]
        print(f'    WIN5フラグ1～5が揃った日数: {len(complete_days)}日')
        if complete_days:
            print(f'    サンプル（最初の10日）:')
            for stat in complete_days[:10]:
                print(f'      {stat["date"]}: レース数={stat["race_count"]}, WIN5フラグ={stat["win5_flags"]}')
        else:
            print(f'    ※WIN5フラグ1～5が揃った日が存在しません')
            print(f'    サンプル（最初の10日）:')
            for stat in date_win5_stats[:10]:
                print(f'      {stat["date"]}: レース数={stat["race_count"]}, WIN5フラグ={stat["win5_flags"]}')
else:
    print('WIN5フラグカラムが存在しません')
    print('  利用可能なカラム（WIN5関連）:')
    win5_cols = [col for col in eval_df_check.columns if 'WIN5' in col or 'win5' in col.lower()]
    print(f'    {win5_cols}')

print()
print('=' * 80)
print('評価結果の妥当性チェック')
print('=' * 80)

# 1着的中率25.38%の場合のWIN5的中確率を計算
first_place_accuracy = 0.2538
win5_probability = first_place_accuracy ** 5
print(f'1着的中率: {first_place_accuracy * 100:.2f}%')
print(f'WIN5的中確率（5レースすべて1着的中、独立と仮定）: {win5_probability * 100:.4f}%')
print(f'  = ({first_place_accuracy:.4f})^5 = {win5_probability:.6f}')
print()

# 実際のレース数から期待値を計算
if 'WIN5フラグ' in eval_df_check.columns and 'race_key' in eval_df_check.columns:
    eval_df_check['date'] = eval_df_check['race_key'].astype(str).str[:8]
    total_days = len(eval_df_check['date'].unique())
    print(f'評価期間の総日数: {total_days}日')
    
    # WIN5フラグ1～5が揃った日数を計算
    complete_days = 0
    for date in eval_df_check['date'].unique():
        date_data = eval_df_check[eval_df_check['date'] == date]
        win5_flags_raw = date_data['WIN5フラグ']
        win5_flags = pd.to_numeric(win5_flags_raw, errors='coerce').dropna().astype(int)
        if len(win5_flags) > 0 and set(win5_flags.unique()) >= {1, 2, 3, 4, 5}:
            complete_days += 1
    
    print(f'WIN5フラグ1～5が揃った日数: {complete_days}日')
    if complete_days > 0:
        expected_wins = complete_days * win5_probability
        print(f'期待WIN5的中日数（独立と仮定）: {expected_wins:.2f}日')
        print(f'  = {complete_days}日 × {win5_probability:.6f} = {expected_wins:.2f}日')
    else:
        print('※WIN5フラグ1～5が揃った日が存在しないため、WIN5評価は実行されていません')

print()
print('=' * 80)
print('データリークの可能性チェック')
print('=' * 80)

# 学習データとテストデータの分割確認
if 'start_datetime' in eval_df_check.columns:
    eval_df_check['date'] = eval_df_check['race_key'].astype(str).str[:8]
    train_dates = set()
    test_dates = set()
    
    # 学習データとテストデータの日付を取得（インデックスから）
    if train_df.index.name == 'race_key':
        train_race_keys = train_df.index.astype(str)
        train_dates = set(train_race_keys.str[:8].unique())
    if test_df.index.name == 'race_key':
        test_race_keys = test_df.index.astype(str)
        test_dates = set(test_race_keys.str[:8].unique())
    
    print(f'学習データの日付数: {len(train_dates)}日')
    print(f'テストデータの日付数: {len(test_dates)}日')
    
    overlap_dates = train_dates & test_dates
    if overlap_dates:
        print(f'⚠️  学習データとテストデータに重複する日付が{len(overlap_dates)}日存在します')
        print(f'  サンプル: {sorted(list(overlap_dates))[:10]}')
    else:
        print(f'✅ 学習データとテストデータに重複する日付は存在しません')

