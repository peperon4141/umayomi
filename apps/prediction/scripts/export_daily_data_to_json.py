"""日次ParquetデータをJSON形式で出力するスクリプト（Firestore保存用）"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd

# プロジェクトルートをパスに追加
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "apps" / "prediction"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def read_parquet_to_dict(parquet_path: Path) -> List[Dict[str, Any]]:
    """Parquetファイルを読み込んで辞書のリストに変換
    
    Args:
        parquet_path: Parquetファイルのパス
    
    Returns:
        レコードのリスト（辞書形式）
    """
    try:
        df = pd.read_parquet(parquet_path)
        # NaNをNoneに変換（JSONシリアライズのため）
        df = df.where(pd.notnull(df), None)
        # DataFrameを辞書のリストに変換
        records = df.to_dict('records')
        return records
    except Exception as e:
        logger.error(f'Parquetファイルの読み込みに失敗しました: {parquet_path}', exc_info=e)
        raise


def export_daily_data_to_json(
    year: int,
    month: int,
    day: int,
    daily_folder: Path
) -> Dict[str, Any]:
    """日次データをJSON形式で出力
    
    Args:
        year: 年
        month: 月
        day: 日
        daily_folder: 日次データフォルダのパス
    
    Returns:
        エクスポート結果の辞書
    """
    date_str = f"{year}-{month:02d}-{day:02d}"
    logger.info(f'日次データのエクスポート開始: {date_str}')
    
    # データタイプのリスト
    data_types = ['BAC', 'KYI', 'UKC', 'TYB']
    
    result = {
        'date': date_str,
        'year': year,
        'month': month,
        'day': day,
        'dataTypes': {}
    }
    
    for data_type in data_types:
        # Parquetファイルを検索
        parquet_files = list(daily_folder.glob(f'{data_type}*.parquet'))
        
        if not parquet_files:
            logger.warning(f'{data_type}のParquetファイルが見つかりません: {daily_folder}')
            result['dataTypes'][data_type] = {
                'success': False,
                'error': 'Parquetファイルが見つかりません',
                'recordCount': 0,
                'records': []
            }
            continue
        
        # 最初のファイルを使用（通常は1つのはず）
        parquet_file = parquet_files[0]
        
        try:
            # Parquetファイルを読み込む
            records = read_parquet_to_dict(parquet_file)
            
            # race_keyでグループ化
            grouped_by_race_key: Dict[str, List[Dict[str, Any]]] = {}
            for record in records:
                race_key = record.get('race_key')
                if race_key:
                    if race_key not in grouped_by_race_key:
                        grouped_by_race_key[race_key] = []
                    grouped_by_race_key[race_key].append(record)
            
            result['dataTypes'][data_type] = {
                'success': True,
                'recordCount': len(records),
                'raceKeyCount': len(grouped_by_race_key),
                'groupedByRaceKey': grouped_by_race_key
            }
            
            logger.info(f'{data_type}のエクスポート完了: {len(records)}件のレコード、{len(grouped_by_race_key)}件のrace_key')
            
        except Exception as e:
            logger.error(f'{data_type}のエクスポートに失敗しました', exc_info=e)
            result['dataTypes'][data_type] = {
                'success': False,
                'error': str(e),
                'recordCount': 0,
                'groupedByRaceKey': {}
            }
    
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='日次ParquetデータをJSON形式で出力')
    parser.add_argument('--date', type=str, help='日付 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--year', type=int, help='年')
    parser.add_argument('--month', type=int, help='月')
    parser.add_argument('--day', type=int, help='日')
    parser.add_argument('--daily-folder', type=str, help='日次データフォルダのパス（省略時は自動計算）')
    
    args = parser.parse_args()
    
    # 日付の決定
    if args.date:
        date_obj = datetime.strptime(args.date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        day = date_obj.day
    elif args.year and args.month and args.day:
        year = args.year
        month = args.month
        day = args.day
    else:
        # デフォルトは今日
        today = datetime.now()
        year = today.year
        month = today.month
        day = today.day
    
    # 日次データフォルダの決定
    if args.daily_folder:
        daily_folder = Path(args.daily_folder)
    else:
        daily_folder = base_path / "data" / "daily" / f"{month:02d}" / f"{day:02d}"
    
    if not daily_folder.exists():
        print(f"❌ エラー: 日次データフォルダが見つかりません: {daily_folder}")
        exit(1)
    
    print(f"=== 日次データのJSONエクスポート ===")
    print(f"  日付: {year}-{month:02d}-{day:02d}")
    print(f"  データフォルダ: {daily_folder}")
    
    # エクスポート実行
    try:
        result = export_daily_data_to_json(year, month, day, daily_folder)
        
        # JSON形式で出力
        print("\n=== エクスポート結果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        exit(1)

