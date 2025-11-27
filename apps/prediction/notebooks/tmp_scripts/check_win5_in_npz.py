#!/usr/bin/env python3
"""NPZファイルから直接WIN5フラグを確認するスクリプト"""

import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data_loader import load_annual_pack_npz

# NPZファイルから直接BACデータを読み込む
npz_dir = project_root / 'notebooks' / 'data'
year = 2024

try:
    print('=' * 80)
    print('BACデータ（NPZ）からWIN5フラグを確認')
    print('=' * 80)
    
    bac_df = load_annual_pack_npz(npz_dir, 'BAC', year)
    
    print(f'BACデータの形状: {bac_df.shape}')
    print()
    
    if 'WIN5フラグ' in bac_df.columns:
        print('WIN5フラグカラムが存在します')
        print(f'  総データ数: {len(bac_df):,}件')
        print(f'  WIN5フラグが存在する行数: {bac_df["WIN5フラグ"].notna().sum():,}件')
        print()
        print(f'  WIN5フラグのデータ型: {bac_df["WIN5フラグ"].dtype}')
        print(f'  WIN5フラグの値の分布（最初の20件）:')
        win5_counts = bac_df['WIN5フラグ'].value_counts().head(20)
        print(win5_counts)
        print()
        print(f'  WIN5フラグのサンプル値（最初の20件）:')
        print(bac_df['WIN5フラグ'].head(20).tolist())
        print()
        
        # 数値に変換可能なWIN5フラグ
        win5_numeric = pd.to_numeric(bac_df['WIN5フラグ'], errors='coerce')
        print(f'  数値に変換可能なWIN5フラグの行数: {win5_numeric.notna().sum():,}件')
        if win5_numeric.notna().sum() > 0:
            print(f'  数値に変換可能なWIN5フラグの値の分布:')
            win5_numeric_counts = win5_numeric.value_counts().sort_index()
            print(win5_numeric_counts)
            print()
            print(f'  WIN5フラグ1～5の値を持つ行数:')
            for i in range(1, 6):
                count = (win5_numeric == i).sum()
                print(f'    WIN5フラグ={i}: {count:,}件')
            
            # 年月日ごとのWIN5フラグ1～5の分布
            if '年月日' in bac_df.columns:
                print()
                print(f'  年月日ごとのWIN5フラグ1～5の分布（最初の30日）:')
                date_win5_stats = []
                for date in sorted(bac_df['年月日'].unique())[:30]:
                    date_data = bac_df[bac_df['年月日'] == date]
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
                        if has_all_flags or len(unique_flags) > 0:
                            print(f'    {date}: レース数={len(date_data)}, WIN5フラグ={unique_flags}, 完全={has_all_flags}')
                
                # WIN5フラグ1～5が揃った日数を計算
                complete_days = sum(1 for s in date_win5_stats if s['has_all_flags'])
                print()
                print(f'  サンプル30日中のWIN5フラグ1～5が揃った日数: {complete_days}日')
                
                # 全期間でWIN5フラグ1～5が揃った日数を計算
                all_complete_days = 0
                for date in sorted(bac_df['年月日'].unique()):
                    date_data = bac_df[bac_df['年月日'] == date]
                    win5_flags_raw = date_data['WIN5フラグ']
                    win5_flags = pd.to_numeric(win5_flags_raw, errors='coerce').dropna().astype(int)
                    if len(win5_flags) > 0:
                        unique_flags = set(win5_flags.unique())
                        if unique_flags >= {1, 2, 3, 4, 5}:
                            all_complete_days += 1
                print(f'  全期間中のWIN5フラグ1～5が揃った日数: {all_complete_days}日')
        else:
            print('  ⚠️  数値に変換可能なWIN5フラグが0件です')
            print('  空文字列やNaNの可能性があります')
    else:
        print('WIN5フラグカラムが存在しません')
        print('  利用可能なカラム（最初の50件）:')
        print(list(bac_df.columns)[:50])
except Exception as e:
    print(f'エラーが発生しました: {e}')
    import traceback
    traceback.print_exc()

