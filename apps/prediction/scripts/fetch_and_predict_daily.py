"""今日のレースデータを取得して予測を実行するスクリプト"""

import sys
import os
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

from src.executor.prediction_executor import PredictionExecutor
from src.jrdb_scraper.fetch_daily_data import fetch_daily_data
from src.jrdb_scraper.entities.jrdb import JRDBDataType

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数の確認
jrdb_username = os.getenv('JRDB_USERNAME')
jrdb_password = os.getenv('JRDB_PASSWORD')

if __name__ == "__main__":
    # 今日の日付を取得
    today = datetime.now()
    year = today.year
    month = today.month
    day = today.day
    date_str = today.strftime("%Y-%m-%d")
    
    # パス設定
    parquet_base_path = base_path / "apps" / "prediction" / "cache" / "jrdb" / "parquet"
    daily_data_path = str(base_path / "data" / "daily")
    model_path = str(base_path / "apps" / "prediction" / "models" / "rank_model_202512111031_v1.txt")
    output_path = str(base_path / "apps" / "prediction" / "output" / f"prediction_results_{date_str}.json")
    
    # 日次データフォルダ
    daily_folder = base_path / "data" / "daily" / f"{month:02d}" / f"{day:02d}"
    
    print(f"=== 日次データ取得・予測実行 ===")
    print(f"  日付: {date_str}")
    print(f"  モデル: {model_path}")
    print(f"  日次データ: {daily_data_path}")
    print(f"  出力先: {output_path}")
    
    # 1. データ取得（データが存在しない場合）
    if not daily_folder.exists() or not list(daily_folder.glob("*.lzh")):
        print(f"\n[1/2] 日次データを取得します...")
        print(f"  データフォルダ: {daily_folder}")
        
        # 環境変数の確認
        if not jrdb_username or not jrdb_password:
            print("\n❌ エラー: JRDB認証情報が設定されていません。")
            print(f"  JRDB_USERNAME: {'設定済み' if jrdb_username else '未設定'}")
            print(f"  JRDB_PASSWORD: {'設定済み' if jrdb_password else '未設定'}")
            print("\n以下の環境変数を設定してください：")
            print("  export JRDB_USERNAME='your_username'")
            print("  export JRDB_PASSWORD='your_password'")
            print("\n設定後、再度このスクリプトを実行してください。")
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
        
        print(f"  取得完了: {success_count}/{len(data_types)} データタイプ")
        if failed_results:
            print(f"  失敗したデータタイプ（オプショナルは問題ありません）:")
            for r in failed_results:
                data_type = r.get('dataType')
                is_optional = data_type in ['UKC', 'TYB']
                marker = "(オプショナル)" if is_optional else "(必須)"
                print(f"    - {data_type} {marker}: {r.get('error', 'Unknown error')}")
        
        # 必須データタイプの確認
        required_failures = [r for r in failed_results if r.get('dataType') in [dt.value for dt in required_data_types]]
        if len(required_failures) > 0:
            print("エラー: 必須データタイプの取得に失敗しました。")
            exit(1)
        
        if success_count > 0:
            print(f"  必須データタイプの取得に成功しました。処理を続行します。")
    else:
        print(f"\n[1/2] 日次データは既に存在します: {daily_folder}")
        lzh_files = list(daily_folder.glob("*.lzh"))
        print(f"  見つかったLZHファイル: {len(lzh_files)}個")
    
    # 2. 予測実行
    print(f"\n[2/2] 予測を実行します...")
    try:
        results_df = PredictionExecutor.execute_daily_prediction(
            date_str=date_str,
            model_path=model_path,
            daily_data_path=daily_data_path,
            base_path=base_path,
            parquet_base_path=parquet_base_path,
            output_path=output_path,
        )
        
        print(f"\n=== 予測実行が完了しました！ ===")
        print(f"  予測結果の行数: {len(results_df)}")
        print(f"  予測結果のカラム: {list(results_df.columns)}")
        print(f"  出力ファイル: {output_path}")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

