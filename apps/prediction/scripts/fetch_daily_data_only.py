"""指定日のJRDBデータを取得するスクリプト（データ取得のみ）"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "apps" / "prediction"))

# .envファイルから環境変数を読み込む
def load_env_file(env_path: Path):
    """.envファイルから環境変数を読み込む"""
    if not env_path.exists():
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # コメント行や空行をスキップ
            if not line or line.startswith('#'):
                continue
            # KEY=VALUE形式を解析
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # クォートを除去
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                # 環境変数が未設定の場合のみ設定
                if key and not os.getenv(key):
                    os.environ[key] = value
    return True

env_path = base_path / "apps" / ".env"
if load_env_file(env_path):
    print(f"環境変数を読み込みました: {env_path}")
else:
    print(f"警告: .envファイルが見つかりません: {env_path}")

from src.jrdb_scraper.fetch_daily_data import fetch_daily_data
from src.jrdb_scraper.entities.jrdb import JRDBDataType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JRDB日次データ取得スクリプト')
    parser.add_argument('--date', type=str, help='日付 (YYYY-MM-DD形式、省略時は今日)')
    parser.add_argument('--year', type=int, help='年')
    parser.add_argument('--month', type=int, help='月')
    parser.add_argument('--day', type=int, help='日')
    
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
    
    date_str = f"{year}-{month:02d}-{day:02d}"
    
    # 日次データフォルダ
    daily_folder = base_path / "data" / "daily" / f"{month:02d}" / f"{day:02d}"
    
    print(f"=== JRDB日次データ取得 ===")
    print(f"  日付: {date_str}")
    print(f"  データフォルダ: {daily_folder}")
    
    # 環境変数の確認
    jrdb_username = os.getenv('JRDB_USERNAME')
    jrdb_password = os.getenv('JRDB_PASSWORD')
    
    if not jrdb_username or not jrdb_password:
        print("\n❌ エラー: JRDB認証情報が設定されていません。")
        print(f"  JRDB_USERNAME: {'設定済み' if jrdb_username else '未設定'}")
        print(f"  JRDB_PASSWORD: {'設定済み' if jrdb_password else '未設定'}")
        exit(1)
    
    print(f"  認証情報: JRDB_USERNAME={jrdb_username[:3]}*** (設定済み)")
    
    # 必要なデータタイプを定義
    required_data_types = [
        JRDBDataType.BAC,  # レース情報（必須）
        JRDBDataType.KYI,  # 騎手・調教師情報（必須）
    ]
    optional_data_types = [
        JRDBDataType.UKC,  # オッズ情報（オプショナル）
        JRDBDataType.TYB,  # 特別登録情報（オプショナル）
    ]
    data_types = required_data_types + optional_data_types
    
    # データ取得を実行
    output_dir = daily_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = fetch_daily_data(year, month, day, data_types, output_dir)
    
    # 結果確認
    success_count = sum(1 for r in results if r.get('success', False))
    failed_results = [r for r in results if not r.get('success', False)]
    
    print(f"\n取得完了: {success_count}/{len(data_types)} データタイプ")
    if failed_results:
        for r in failed_results:
            data_type = r.get('dataType')
            is_optional = data_type in ['UKC', 'TYB']
            marker = "(オプショナル)" if is_optional else "(必須)"
            print(f"  - {data_type} {marker}: {r.get('error', 'Unknown error')}")
    
    # 必須データタイプの確認
    required_failures = [r for r in failed_results if r.get('dataType') in [dt.value for dt in required_data_types]]
    if len(required_failures) > 0:
        print("\n❌ エラー: 必須データタイプの取得に失敗しました。")
        exit(1)
    
    print("\n✅ データ取得が完了しました。")
    
    # 結果をJSON形式で出力（Cloud Functionから読み取れるように）
    import json
    result_summary = {
        'success': len(required_failures) == 0,
        'date': date_str,
        'totalDataTypes': len(data_types),
        'successCount': success_count,
        'results': results
    }
    print("\n=== 結果サマリー ===")
    print(json.dumps(result_summary, indent=2, ensure_ascii=False))

