#!/usr/bin/env python3
"""データのカラムを確認するスクリプト"""

import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data_processer import DataProcessor

base_project_path = Path(__file__).resolve().parent.parent
data_processor = DataProcessor(base_path=base_project_path.parent.parent)

DATA_TYPES = ['BAC', 'KYI', 'SED', 'UKC', 'TYB']
YEAR = 2024
SPLIT_DATE = '2024-06-01'

# キャッシュから読み込み
train_df, test_df, eval_df = data_processor.process(
    data_types=DATA_TYPES,
    year=YEAR,
    split_date=SPLIT_DATE,
)

print('=' * 80)
print('学習データのカラム（prev関連）:')
prev_cols_train = [col for col in train_df.columns if 'prev' in col.lower()]
print(f'  見つかったprev関連カラム: {len(prev_cols_train)}件')
if prev_cols_train:
    print(f'  サンプル: {prev_cols_train[:10]}')
print()

print('学習データのカラム（race_key関連）:')
race_key_cols_train = [col for col in train_df.columns if 'race_key' in col.lower()]
print(f'  見つかったrace_key関連カラム: {len(race_key_cols_train)}件')
if race_key_cols_train:
    print(f'  サンプル: {race_key_cols_train[:10]}')
print()

print('=' * 80)
print('評価用データのカラム（prev関連）:')
prev_cols_eval = [col for col in eval_df.columns if 'prev' in col.lower()]
print(f'  見つかったprev関連カラム: {len(prev_cols_eval)}件')
if prev_cols_eval:
    print(f'  サンプル: {prev_cols_eval[:10]}')
print()

print('評価用データのカラム（race_key関連）:')
race_key_cols_eval = [col for col in eval_df.columns if 'race_key' in col.lower()]
print(f'  見つかったrace_key関連カラム: {len(race_key_cols_eval)}件')
if race_key_cols_eval:
    print(f'  サンプル: {race_key_cols_eval[:10]}')
print()

print('=' * 80)
print('評価用データの全カラム数:', len(eval_df.columns))
print('評価用データのカラム（最初の30件）:', list(eval_df.columns)[:30])

