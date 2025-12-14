"""Firestoreへの予測結果保存機能"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    raise ImportError("firebase-adminがインストールされていません。pip install firebase-admin でインストールしてください。")

logger = logging.getLogger(__name__)

# Firebase Admin SDKの初期化（一度だけ実行）
_initialized = False


def _initialize_firebase():
    """Firebase Admin SDKを初期化"""
    global _initialized
    if _initialized:
        return
    
    # 環境変数から認証情報を取得
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    use_emulator = os.getenv('USE_FIREBASE_EMULATOR', 'false').lower() == 'true'
    
    if use_emulator:
        # エミュレーター環境
        os.environ['FIRESTORE_EMULATOR_HOST'] = os.getenv('FIRESTORE_EMULATOR_HOST', '127.0.0.1:8180')
        logger.info("Firestoreエミュレーターを使用: 127.0.0.1:8180")
        
        # エミュレーター用の認証情報（ダミー）
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                options={'projectId': 'umayomi-fbb2b'}
            )
    else:
        # 本番環境
        if cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
        else:
            # デフォルト認証情報を使用（GCP環境など）
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
    
    _initialized = True
    logger.info("Firebase Admin SDKを初期化しました")


def save_predictions_to_firestore(
    date_str: str,
    predictions: List[Dict[str, Any]],
    collection_name: str = "predictions"
) -> int:
    """
    予測結果をFirestoreに保存
    
    Args:
        date_str: 日付文字列（YYYY-MM-DD形式）
        predictions: 予測結果のリスト
        collection_name: Firestoreコレクション名（デフォルト: "predictions"）
    
    Returns:
        保存されたドキュメント数
    """
    _initialize_firebase()
    
    db = firestore.client()
    collection = db.collection(collection_name)
    
    # 日付ごとにドキュメントを作成
    doc_id = f"date_{date_str.replace('-', '_')}"
    doc_ref = collection.document(doc_id)
    
    # 予測結果を保存
    data = {
        'date': date_str,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'predictions': predictions,
        'total_count': len(predictions)
    }
    
    logger.info(f"予測結果をFirestoreに保存中: {collection_name}/{doc_id} ({len(predictions)}件)")
    doc_ref.set(data, merge=True)
    
    logger.info(f"予測結果の保存完了: {collection_name}/{doc_id}")
    return 1


def get_predictions_from_firestore(
    date_str: str,
    collection_name: str = "predictions"
) -> Optional[Dict[str, Any]]:
    """
    Firestoreから予測結果を取得
    
    Args:
        date_str: 日付文字列（YYYY-MM-DD形式）
        collection_name: Firestoreコレクション名（デフォルト: "predictions"）
    
    Returns:
        予測結果の辞書（存在しない場合はNone）
    """
    _initialize_firebase()
    
    db = firestore.client()
    collection = db.collection(collection_name)
    
    doc_id = f"date_{date_str.replace('-', '_')}"
    doc_ref = collection.document(doc_id)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        logger.info(f"予測結果を取得: {collection_name}/{doc_id} ({data.get('total_count', 0)}件)")
        return data
    else:
        logger.warning(f"予測結果が見つかりません: {collection_name}/{doc_id}")
        return None

