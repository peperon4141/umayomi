"""data/annual/2024からapps/prediction/cache/jrdb/parquetに変換するスクリプト"""

import sys
from pathlib import Path

# パス設定
PREDICTION_APP_DIRECTORY = Path(__file__).resolve().parent.parent
PROJECT_ROOT_DIRECTORY = PREDICTION_APP_DIRECTORY.parent.parent
sys.path.insert(0, str(PREDICTION_APP_DIRECTORY))

from src.jrdb_scraper.convert_local_folder_to_parquet import convert_local_folder_to_parquet
from src.jrdb_scraper.entities.jrdb import JRDBDataType, get_all_data_types

# 設定
INPUT_FOLDER = PROJECT_ROOT_DIRECTORY / 'data' / 'annual' / '2024'
OUTPUT_DIR = PREDICTION_APP_DIRECTORY / 'cache' / 'jrdb' / 'parquet'
YEAR = 2024

# 全てのデータタイプを取得（年度パックをサポートしているもののみ処理される）
all_data_types = get_all_data_types()

print(f"入力フォルダ: {INPUT_FOLDER}")
print(f"出力ディレクトリ: {OUTPUT_DIR}")
print(f"年度: {YEAR}")
print(f"データタイプ数: {len(all_data_types)}")
print()

# 変換実行
results = convert_local_folder_to_parquet(
    folderPath=INPUT_FOLDER,
    year=YEAR,
    dataTypes=all_data_types,
    outputDir=OUTPUT_DIR
)

# 結果表示
print("\n=== 変換結果 ===")
success_count = 0
for result in results:
    status = "✓" if result.get('success', False) else "✗"
    data_type = result.get('dataType', 'unknown')
    record_count = result.get('recordCount', 0)
    
    if result.get('success', False):
        success_count += 1
        print(f"{status} {data_type}: {record_count:,}件 - {result.get('outputPath', '')}")
    else:
        error = result.get('error', 'Unknown error')
        print(f"{status} {data_type}: エラー - {error}")

print(f"\n成功: {success_count}/{len(results)}")

