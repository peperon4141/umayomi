#!/usr/bin/env python3
"""ノートブックの実行スクリプト"""
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.preprocessor import Preprocessor

BASE_PATH = Path('./notebooks/data')
DATA_TYPES = ['BAC', 'KYI', 'SEC', 'UKC', 'TYB']
YEARS = [2024]

print('データ読み込みを開始します...')
preprocessor = Preprocessor()
df = preprocessor.process(
    base_path=BASE_PATH,
    data_types=DATA_TYPES,
    years=YEARS,
    use_annual_pack=True
)
print(f'データ読み込み完了: {len(df)}件')
print(f'レース数: {df.index.nunique()}')




