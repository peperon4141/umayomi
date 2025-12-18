"""当日の競馬データを取得して予測実行し、Firestoreに保存するスクリプト"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "apps" / "prediction"))

from src.executor.prediction_executor import PredictionExecutor
from src.jrdb_scraper.fetch_daily_data import fetch_daily_data
from src.jrdb_scraper.entities.jrdb import JRDBDataType
from src.utils.firebase_storage import download_model_from_storage
from src.utils.firestore_saver import save_predictions_to_firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .envファイルから環境変数を読み込む
def load_env_file(env_path: Path):
    """.envファイルから環境変数を読み込む"""
    if not env_path.exists():
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                if key and not os.getenv(key):
                    os.environ[key] = value
    return True

env_path = base_path / "apps" / ".env"
if load_env_file(env_path):
    print(f"環境変数を読み込みました: {env_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='当日の競馬データを取得して予測実行し、Firestoreに保存')
    parser.add_argument('--date', help='予測対象日付（YYYY-MM-DD形式、省略時は今日）')
    parser.add_argument('--model-storage-path', required=True, help='Firebase Storage内のモデルパス（例: models/rank_model_202512111031_v1.txt）')
    parser.add_argument('--use-emulator', action='store_true', help='Firebaseエミュレーターを使用')
    parser.add_argument('--json-indent', type=int, default=2, help='JSON出力のインデント（デフォルト: 2）')
    
    args = parser.parse_args()
    
    # 日付の決定
    if args.date:
        date_str = args.date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"エラー: 日付形式が正しくありません。YYYY-MM-DD形式で指定してください。")
            exit(1)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date_obj = datetime.now()
        date_str = date_obj.strftime("%Y-%m-%d")
    
    # Firebaseエミュレーター設定
    if args.use_emulator:
        os.environ['USE_FIREBASE_EMULATOR'] = 'true'
        os.environ['STORAGE_EMULATOR_HOST'] = '127.0.0.1:9198'
        os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8180'
    
    print(f"=== 予測実行・Firestore保存 ===")
    print(f"  日付: {date_str}")
    print(f"  モデルStorageパス: {args.model_storage_path}")
    
    # パス設定
    parquet_base_path = base_path / "apps" / "prediction" / "cache" / "jrdb" / "parquet"
    daily_data_path = str(base_path / "data" / "daily")
    model_cache_path = base_path / "apps" / "prediction" / "cache" / "models"
    model_cache_path.mkdir(parents=True, exist_ok=True)
    
    # 1. モデルをStorageからダウンロード
    print(f"\n[1/5] モデルをFirebase Storageからダウンロード...")
    model_filename = Path(args.model_storage_path).name
    local_model_path = model_cache_path / model_filename
    
    try:
        download_model_from_storage(args.model_storage_path, str(local_model_path))
        print(f"  ✓ モデルダウンロード完了: {local_model_path}")
    except Exception as e:
        print(f"  ✗ モデルダウンロードエラー: {e}")
        exit(1)
    
    # 2. 日次データ取得（データが存在しない場合）
    print(f"\n[2/5] 日次データを取得...")
    daily_folder = base_path / "data" / "daily" / f"{date_obj.month:02d}" / f"{date_obj.day:02d}"
    
    if not daily_folder.exists() or not list(daily_folder.glob("*.lzh")):
        print(f"  データフォルダ: {daily_folder}")
        
        # 環境変数の確認
        jrdb_username = os.getenv('JRDB_USERNAME')
        jrdb_password = os.getenv('JRDB_PASSWORD')
        
        if not jrdb_username or not jrdb_password:
            print("\n❌ エラー: JRDB認証情報が設定されていません。")
            exit(1)
        
        # 必要なデータタイプを定義
        required_data_types = [JRDBDataType.BAC, JRDBDataType.KYI]
        optional_data_types = [JRDBDataType.UKC, JRDBDataType.TYB]
        data_types = required_data_types + optional_data_types
        
        # データ取得を実行
        output_dir = daily_folder
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = fetch_daily_data(date_obj.year, date_obj.month, date_obj.day, data_types, output_dir)
        
        # 結果確認
        success_count = sum(1 for r in results if r.get('success', False))
        failed_results = [r for r in results if not r.get('success', False)]
        
        print(f"  取得完了: {success_count}/{len(data_types)} データタイプ")
        if failed_results:
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
    else:
        print(f"  日次データは既に存在します: {daily_folder}")
    
    # 3. 予測実行
    print(f"\n[3/5] 予測を実行...")
    try:
        results_df = PredictionExecutor.execute_daily_prediction(
            date_str=date_str,
            model_path=str(local_model_path),
            daily_data_path=daily_data_path,
            base_path=base_path,
            parquet_base_path=parquet_base_path,
            output_path=None,  # JSONファイルは保存しない
            json_indent=args.json_indent,
        )
        print(f"  ✓ 予測実行完了: {len(results_df)}件")
    except Exception as e:
        print(f"  ✗ 予測実行エラー: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    # 4. 予測結果をFirestore形式に変換
    print(f"\n[4/5] 予測結果をFirestore形式に変換...")
    predictions = []
    for _, row in results_df.iterrows():
        year = int(date_str.split("-")[0])
        prediction = {
            "race_key": str(row.get("race_key", "")),
            "year": year,
            "race_date": date_str,
            "horse_number": int(row.get("horse_number", 0)),
            "horse_name": str(row.get("horse_name", "")),
            "jockey_name": str(row.get("jockey_name", "")),
            "trainer_name": str(row.get("trainer_name", "")),
            "predicted_score": float(row.get("predicted_score", 0.0)),
            "predicted_rank": int(row.get("predicted_rank", 0)),
        }
        predictions.append(prediction)
    
    print(f"  ✓ 変換完了: {len(predictions)}件")
    
    # 5. Firestoreに保存
    print(f"\n[5/5] 予測結果をFirestoreに保存...")
    try:
        save_predictions_to_firestore(date_str, predictions)
        print(f"  ✓ Firestore保存完了")
    except Exception as e:
        print(f"  ✗ Firestore保存エラー: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    print(f"\n=== すべての処理が完了しました！ ===")
    print(f"  日付: {date_str}")
    print(f"  予測結果数: {len(predictions)}")
    print(f"  Firestoreコレクション: predictions/date_{date_str.replace('-', '_')}")

