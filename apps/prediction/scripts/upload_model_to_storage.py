"""モデルファイルをFirebase Storageにアップロードするスクリプト"""

import sys
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "apps" / "prediction"))

from src.utils.firebase_storage import upload_model_to_storage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='モデルファイルをFirebase Storageにアップロード')
    parser.add_argument('model_path', help='アップロードするモデルファイルのパス')
    parser.add_argument('--storage-path', help='Storage内のパス（省略時は models/ファイル名）')
    parser.add_argument('--use-emulator', action='store_true', help='Firebaseエミュレーターを使用')
    parser.add_argument('--model-name', help='モデル名（Firestore保存時、省略時はファイル名を使用）')
    parser.add_argument('--version', help='バージョン（オプション）')
    parser.add_argument('--description', help='説明（オプション）')
    parser.add_argument('--training-date', help='学習日付（YYYY-MM-DD形式、オプション）')
    parser.add_argument('--no-firestore', action='store_true', help='Firestoreへのメタデータ保存をスキップ')
    
    args = parser.parse_args()
    
    if args.use_emulator:
        import os
        os.environ['USE_FIREBASE_EMULATOR'] = 'true'
        os.environ['STORAGE_EMULATOR_HOST'] = '127.0.0.1:9198'
        os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8180'
    
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"エラー: モデルファイルが見つかりません: {model_path}")
        exit(1)
    
    try:
        url = upload_model_to_storage(
            str(model_path),
            storage_path=args.storage_path,
            metadata={'model_name': model_path.name},
            save_to_firestore=not args.no_firestore,
            model_name=args.model_name,
            version=args.version,
            description=args.description,
            training_date=args.training_date
        )
        print(f"\n✓ モデルファイルのアップロード完了")
        print(f"  Storage URL: {url}")
        if not args.no_firestore:
            print(f"  Firestoreにメタデータを保存しました")
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

