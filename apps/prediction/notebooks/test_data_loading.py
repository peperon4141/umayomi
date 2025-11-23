# データ読み込み部分のテスト
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.training_data_processor import CacheManager

BASE_PATH = Path(__file__).parent / 'data'
DATA_TYPES = ['BAC', 'KYI', 'SED', 'UKC', 'TYB']
YEARS = [2024]
split_date = "2024-06-01"

cache_manager = CacheManager(base_path=project_root)
print("データ読み込みと前処理を開始します...")

try:
    train_df, test_df, original_df = cache_manager.get_or_create(
        data_name="training-data",
        base_path=BASE_PATH,
        data_types=DATA_TYPES,
        years=YEARS,
        split_date=split_date,
    )
    
    print(f"\n前処理完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
    print(f"データ形状: 学習={train_df.shape}, テスト={test_df.shape}")
    
    if 'rank' not in train_df.columns:
        print("ERROR: train_dfにrank列が含まれていません")
    else:
        train_rank_count = train_df['rank'].notna().sum()
        print(f"train_dfのrank列: {train_rank_count:,}件")
    
    if 'rank' not in test_df.columns:
        print("ERROR: test_dfにrank列が含まれていません")
    else:
        test_rank_count = test_df['rank'].notna().sum()
        print(f"test_dfのrank列: {test_rank_count:,}件")
    
    print(f"original_dfのカラム数: {len(original_df.columns)}")
    print(f"original_dfのサンプルカラム: {list(original_df.columns[:10])}")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
    raise

