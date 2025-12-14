"""Firebase Storageへのモデルアップロード・ダウンロード機能"""

import logging
import os
from pathlib import Path
from typing import Optional

try:
    import firebase_admin
    from firebase_admin import credentials, storage
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
        storage_emulator_host = os.getenv('STORAGE_EMULATOR_HOST', '127.0.0.1:9198')
        os.environ['STORAGE_EMULATOR_HOST'] = storage_emulator_host
        logger.info(f"Firebase Storageエミュレーターを使用: {storage_emulator_host}")
        
        # エミュレーター用の認証情報（ダミー）
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                options={'storageBucket': 'umayomi-fbb2b.firebasestorage.app', 'projectId': 'umayomi-fbb2b'}
            )
    else:
        # 本番環境
        if cred_path and Path(cred_path).exists():
            cred = credentials.Certificate(cred_path)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'umayomi-fbb2b.firebasestorage.app')
                })
        else:
            # デフォルト認証情報を使用（GCP環境など）
            if not firebase_admin._apps:
                firebase_admin.initialize_app()
    
    _initialized = True
    logger.info("Firebase Admin SDKを初期化しました")


def upload_model_to_storage(
    local_model_path: str,
    storage_path: Optional[str] = None,
    metadata: Optional[dict] = None
) -> str:
    """
    モデルファイルをFirebase Storageにアップロード
    
    Args:
        local_model_path: ローカルのモデルファイルパス
        storage_path: Storage内のパス（省略時はファイル名を使用）
        metadata: メタデータ（オプション）
    
    Returns:
        アップロードされたファイルのStorage URL
    """
    _initialize_firebase()
    
    local_path = Path(local_model_path)
    if not local_path.exists():
        raise FileNotFoundError(f"モデルファイルが見つかりません: {local_model_path}")
    
    # Storageパスが指定されていない場合は、ファイル名を使用
    if storage_path is None:
        storage_path = f"models/{local_path.name}"
    
    use_emulator = os.getenv('USE_FIREBASE_EMULATOR', 'false').lower() == 'true'
    
    if use_emulator:
        # エミュレーター環境: Google Cloud Storageクライアントを直接使用
        storage_emulator_host = os.getenv('STORAGE_EMULATOR_HOST', '127.0.0.1:9198')
        client = gcs_storage.Client(
            project='umayomi-fbb2b',
            client_options={'api_endpoint': f'http://{storage_emulator_host}'}
        )
        bucket = client.bucket('umayomi-fbb2b.firebasestorage.app')
    else:
        # 本番環境: Firebase Admin SDKを使用
        bucket = storage.bucket()
    
    blob = bucket.blob(storage_path)
    
    # メタデータを設定
    if metadata:
        blob.metadata = metadata
    
    # ファイルをアップロード
    logger.info(f"モデルファイルをアップロード中: {local_path} -> {storage_path}")
    blob.upload_from_filename(str(local_path))
    
    # 公開URLを取得（エミュレーターの場合は直接URLを構築）
    if use_emulator:
        url = f"http://{storage_emulator_host}/umayomi-fbb2b.firebasestorage.app/{storage_path}"
    else:
        blob.make_public()
        url = blob.public_url
    
    logger.info(f"モデルファイルのアップロード完了: {url}")
    return url


def download_model_from_storage(
    storage_path: str,
    local_output_path: str
) -> Path:
    """
    Firebase Storageからモデルファイルをダウンロード
    
    Args:
        storage_path: Storage内のパス
        local_output_path: ローカルの出力パス
    
    Returns:
        ダウンロードされたファイルのパス
    """
    _initialize_firebase()
    
    use_emulator = os.getenv('USE_FIREBASE_EMULATOR', 'false').lower() == 'true'
    
    if use_emulator:
        # エミュレーター環境: Google Cloud Storageクライアントを直接使用
        storage_emulator_host = os.getenv('STORAGE_EMULATOR_HOST', '127.0.0.1:9198')
        client = gcs_storage.Client(
            project='umayomi-fbb2b',
            client_options={'api_endpoint': f'http://{storage_emulator_host}'}
        )
        bucket = client.bucket('umayomi-fbb2b.firebasestorage.app')
    else:
        # 本番環境: Firebase Admin SDKを使用
        bucket = storage.bucket()
    
    blob = bucket.blob(storage_path)
    
    if not blob.exists():
        raise FileNotFoundError(f"Storage内にファイルが見つかりません: {storage_path}")
    
    output_path = Path(local_output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"モデルファイルをダウンロード中: {storage_path} -> {output_path}")
    blob.download_to_filename(str(output_path))
    
    logger.info(f"モデルファイルのダウンロード完了: {output_path}")
    return output_path


def list_models_in_storage(prefix: str = "models/") -> list[dict]:
    """
    Storage内のモデルファイル一覧を取得
    
    Args:
        prefix: プレフィックス（デフォルト: "models/"）
    
    Returns:
        モデルファイル情報のリスト
    """
    _initialize_firebase()
    
    use_emulator = os.getenv('USE_FIREBASE_EMULATOR', 'false').lower() == 'true'
    
    if use_emulator:
        # エミュレーター環境: Google Cloud Storageクライアントを直接使用
        storage_emulator_host = os.getenv('STORAGE_EMULATOR_HOST', '127.0.0.1:9198')
        client = gcs_storage.Client(
            project='umayomi-fbb2b',
            client_options={'api_endpoint': f'http://{storage_emulator_host}'}
        )
        bucket = client.bucket('umayomi-fbb2b.firebasestorage.app')
    else:
        # 本番環境: Firebase Admin SDKを使用
        bucket = storage.bucket()
    
    blobs = bucket.list_blobs(prefix=prefix)
    
    models = []
    for blob in blobs:
        if use_emulator:
            url = f"http://{storage_emulator_host}/umayomi-fbb2b.firebasestorage.app/{blob.name}"
        else:
            url = blob.public_url if blob.public_url else None
        
        models.append({
            'name': blob.name,
            'size': blob.size,
            'created': blob.time_created,
            'updated': blob.updated,
            'url': url
        })
    
    return models

