#!/usr/bin/env python3
"""featured_dfのWIN5フラグを確認するスクリプト"""

import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# キャッシュからfeatured_dfを読み込む
cache_dir = project_root / 'cache'
featured_cache = cache_dir / 'BAC_KYI_SED_TYB_UKC_2024_featured_data.parquet'

if featured_cache.exists():
    print('=' * 80)
    print('featured_dfをキャッシュから読み込み中...')
    featured_df = pd.read_parquet(featured_cache)
    print(f'featured_dfの形状: {featured_df.shape}')
    print()
    
    if 'WIN5フラグ' in featured_df.columns:
        print('WIN5フラグカラムが存在します')
        print(f'  総データ数: {len(featured_df):,}件')
        print(f'  WIN5フラグが存在する行数: {featured_df["WIN5フラグ"].notna().sum():,}件')
        print()
        print(f'  WIN5フラグのデータ型: {featured_df["WIN5フラグ"].dtype}')
        print(f'  WIN5フラグの値の分布（最初の20件）:')
        win5_counts = featured_df['WIN5フラグ'].value_counts().head(20)
        print(win5_counts)
        print()
        print(f'  WIN5フラグのサンプル値（最初の20件）:')
        print(featured_df['WIN5フラグ'].head(20).tolist())
        print()
        
        # 空文字列を除外
        win5_non_empty = featured_df[featured_df['WIN5フラグ'].astype(str).str.strip() != '']
        print(f'  空文字列以外のWIN5フラグの行数: {len(win5_non_empty):,}件')
        if len(win5_non_empty) > 0:
            print(f'  空文字列以外のWIN5フラグの値の分布:')
            win5_non_empty_counts = win5_non_empty['WIN5フラグ'].value_counts().sort_index()
            print(win5_non_empty_counts)
            print()
        
        # 数値に変換可能なWIN5フラグ
        win5_numeric = pd.to_numeric(featured_df['WIN5フラグ'], errors='coerce')
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
            
            # 日付ごとのWIN5フラグ1～5の分布
            if 'race_key' in featured_df.columns or featured_df.index.name == 'race_key':
                featured_df_check = featured_df.reset_index() if featured_df.index.name == 'race_key' else featured_df.copy()
                if 'race_key' in featured_df_check.columns:
                    featured_df_check['date'] = featured_df_check['race_key'].astype(str).str[:8]
                    print()
                    print(f'  日付ごとのWIN5フラグ1～5の分布（最初の20日）:')
                    date_win5_stats = []
                    for date in sorted(featured_df_check['date'].unique())[:20]:
                        date_data = featured_df_check[featured_df_check['date'] == date]
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
                            print(f'    {date}: レース数={len(date_data)}, WIN5フラグ={unique_flags}, 完全={has_all_flags}')
    else:
        print('WIN5フラグカラムが存在しません')
        print('  利用可能なカラム（WIN5関連）:')
        win5_cols = [col for col in featured_df.columns if 'WIN5' in col or 'win5' in col.lower()]
        print(f'    {win5_cols}')
        print()
        print('  利用可能なカラム（最初の50件）:')
        print(list(featured_df.columns)[:50])
else:
    print(f'featured_dfのキャッシュが見つかりません: {featured_cache}')
    print('  利用可能なキャッシュファイル:')
    if cache_dir.exists():
        cache_files = list(cache_dir.glob('*.parquet'))
        for f in cache_files[:10]:
            print(f'    {f.name}')

