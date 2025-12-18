"""モデルメタデータをFirestoreエミュレーターに直接保存するスクリプト"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "apps" / "prediction"))

from src.utils.firestore_saver import save_model_metadata_to_firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='モデルメタデータをFirestoreエミュレーターに保存')
    parser.add_argument('--model-name', required=True, help='モデル名')
    parser.add_argument('--storage-path', required=True, help='Storage内のパス')
    parser.add_argument('--storage-url', required=True, help='Storage URL')
    parser.add_argument('--version', help='バージョン（オプション）')
    parser.add_argument('--description', help='説明（オプション）')
    parser.add_argument('--training-date', help='学習日付（YYYY-MM-DD形式、オプション）')
    
    args = parser.parse_args()
    
    # エミュレーター環境を設定
    os.environ['USE_FIREBASE_EMULATOR'] = 'true'
    os.environ['STORAGE_EMULATOR_HOST'] = '127.0.0.1:9198'
    os.environ['FIRESTORE_EMULATOR_HOST'] = '127.0.0.1:8180'
    os.environ['GCLOUD_PROJECT'] = 'umayomi-fbb2b'
    
    try:
        doc_id = save_model_metadata_to_firestore(
            model_name=args.model_name,
            storage_path=args.storage_path,
            storage_url=args.storage_url,
            version=args.version,
            description=args.description,
            training_date=args.training_date
        )
        print(f"\n✓ モデルメタデータの保存完了")
        print(f"  FirestoreドキュメントID: {doc_id}")
    except Exception as e:
        print(f"\n✗ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

