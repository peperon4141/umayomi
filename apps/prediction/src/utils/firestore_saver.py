"""Firestoreへの予測結果保存機能"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.request import Request, urlopen

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:
    raise ImportError("firebase-adminがインストールされていません。pip install firebase-admin でインストールしてください。")

logger = logging.getLogger(__name__)

# Firebase Admin SDKの初期化（一度だけ実行）
_initialized = False


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is required (no fallback).")
    return value


def _get_project_id() -> str:
    direct = os.getenv("GCLOUD_PROJECT")
    if direct:
        return direct
    firebase_config = os.getenv("FIREBASE_CONFIG")
    if firebase_config:
        try:
            parsed = json.loads(firebase_config)
        except Exception as e:
            raise ValueError("FIREBASE_CONFIG must be a valid JSON string.") from e
        project_id = parsed.get("projectId")
        if isinstance(project_id, str) and project_id:
            return project_id
        raise ValueError("FIREBASE_CONFIG.projectId is required (no fallback).")
    raise ValueError("GCLOUD_PROJECT (or FIREBASE_CONFIG) is required (no fallback).")


def _use_emulator() -> bool:
    return os.getenv('USE_FIREBASE_EMULATOR', 'false').lower() == 'true'


def _firestore_emulator_doc_url(collection_name: str, doc_id: str) -> str:
    host = _require_env('FIRESTORE_EMULATOR_HOST')
    project_id = _get_project_id()
    return f"http://{host}/v1/projects/{project_id}/databases/(default)/documents/{collection_name}/{doc_id}"


def _to_firestore_value(value: Any) -> Dict[str, Any]:
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, str):
        return {"stringValue": value}
    raise ValueError(f"Unsupported Firestore value type: {type(value)}")


def _to_firestore_map(fields: Dict[str, Any]) -> Dict[str, Any]:
    return {"mapValue": {"fields": {k: _to_firestore_value(v) for k, v in fields.items()}}}


def _patch_firestore_doc(url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    payload = json.dumps(body).encode('utf-8')
    req = Request(url, data=payload, method='PATCH')
    req.add_header('Content-Type', 'application/json')
    # Firestore Emulatorはこのトークンを受け付ける（認証情報不要）
    req.add_header('Authorization', 'Bearer owner')
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _initialize_firebase():
    """Firebase Admin SDKを初期化"""
    global _initialized
    if _initialized:
        return
    
    # 環境変数から認証情報を取得
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    use_emulator = _use_emulator()
    
    if use_emulator:
        # エミュレーター環境では、FirestoreはRESTで保存する（ADC不要・fallback禁止）。
        # firebase_admin.firestore.client() はADCを要求し、ローカルでは失敗し得るためここでは初期化しない。
        firestore_emulator_host = _require_env('FIRESTORE_EMULATOR_HOST')
        _require_env('GCLOUD_PROJECT')
        logger.info(f"Firestoreエミュレーターを使用: {firestore_emulator_host}")
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
    doc_id = f"date_{date_str.replace('-', '_')}"
    logger.info(f"予測結果をFirestoreに保存中: {collection_name}/{doc_id} ({len(predictions)}件)")

    if _use_emulator():
        now = datetime.utcnow().isoformat(timespec='seconds') + "Z"
        body = {
            "fields": {
                "date": {"stringValue": date_str},
                "total_count": {"integerValue": str(len(predictions))},
                "created_at": {"timestampValue": now},
                "updated_at": {"timestampValue": now},
                "predictions": {
                    "arrayValue": {
                        "values": [
                            _to_firestore_map({
                                "race_key": p["race_key"],
                                "horse_number": int(p["horse_number"]),
                                "horse_name": p["horse_name"],
                                "jockey_name": p["jockey_name"],
                                "trainer_name": p["trainer_name"],
                                "predicted_score": float(p["predicted_score"]),
                                "predicted_rank": int(p["predicted_rank"]),
                            })
                            for p in predictions
                        ]
                    }
                },
            }
        }
        url = _firestore_emulator_doc_url(collection_name, doc_id)
        _patch_firestore_doc(url, body)
        logger.info(f"予測結果の保存完了: {collection_name}/{doc_id}")
        return 1

    _initialize_firebase()
    db = firestore.client()
    collection = db.collection(collection_name)
    doc_ref = collection.document(doc_id)

    # 予測結果を保存
    data = {
        'date': date_str,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'predictions': predictions,
        'total_count': len(predictions)
    }

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


def save_model_metadata_to_firestore(
    model_name: str,
    storage_path: str,
    storage_url: str,
    version: Optional[str] = None,
    description: Optional[str] = None,
    performance_metrics: Optional[Dict[str, Any]] = None,
    training_date: Optional[str] = None,
    collection_name: str = "models"
) -> str:
    """
    モデルメタデータをFirestoreに保存
    
    Args:
        model_name: モデル名
        storage_path: Storage内のパス
        storage_url: Storage URL
        version: バージョン（オプション）
        description: 説明（オプション）
        performance_metrics: パフォーマンス指標（オプション）
        training_date: 学習日付（YYYY-MM-DD形式、オプション）
        collection_name: Firestoreコレクション名（デフォルト: "models"）
    
    Returns:
        保存されたドキュメントID
    """
    doc_id = model_name
    logger.info(f"モデルメタデータをFirestoreに保存中: {collection_name}/{doc_id}")

    if _use_emulator():
        if performance_metrics is not None:
            raise ValueError("performance_metrics is not supported in emulator REST saver yet (no silent fallback).")
        now = datetime.utcnow().isoformat(timespec='seconds') + "Z"
        fields: Dict[str, Any] = {
            "model_name": {"stringValue": model_name},
            "storage_path": {"stringValue": storage_path},
            "storage_url": {"stringValue": storage_url},
            "created_at": {"timestampValue": now},
            "updated_at": {"timestampValue": now},
        }
        if version:
            fields["version"] = {"stringValue": version}
        if description:
            fields["description"] = {"stringValue": description}
        if training_date:
            fields["training_date"] = {"stringValue": training_date}
        url = _firestore_emulator_doc_url(collection_name, doc_id)
        _patch_firestore_doc(url, {"fields": fields})
        logger.info(f"モデルメタデータの保存完了: {collection_name}/{doc_id}")
        return doc_id

    _initialize_firebase()
    db = firestore.client()
    collection = db.collection(collection_name)
    doc_ref = collection.document(doc_id)

    data = {
        'model_name': model_name,
        'storage_path': storage_path,
        'storage_url': storage_url,
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
    }

    if version:
        data['version'] = version
    if description:
        data['description'] = description
    if performance_metrics:
        data['performance_metrics'] = performance_metrics
    if training_date:
        data['training_date'] = training_date

    doc_ref.set(data, merge=True)
    logger.info(f"モデルメタデータの保存完了: {collection_name}/{doc_id}")
    return doc_id


def get_model_metadata_from_firestore(
    model_name: str,
    collection_name: str = "models"
) -> Optional[Dict[str, Any]]:
    """
    Firestoreからモデルメタデータを取得
    
    Args:
        model_name: モデル名
        collection_name: Firestoreコレクション名（デフォルト: "models"）
    
    Returns:
        モデルメタデータの辞書（存在しない場合はNone）
    """
    _initialize_firebase()
    
    db = firestore.client()
    collection = db.collection(collection_name)
    
    doc_ref = collection.document(model_name)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        logger.info(f"モデルメタデータを取得: {collection_name}/{model_name}")
        return data
    else:
        logger.warning(f"モデルメタデータが見つかりません: {collection_name}/{model_name}")
        return None


def list_models_from_firestore(
    collection_name: str = "models",
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Firestoreからモデル一覧を取得
    
    Args:
        collection_name: Firestoreコレクション名（デフォルト: "models"）
        limit: 取得件数の上限（オプション）
    
    Returns:
        モデルメタデータのリスト（作成日時の降順）
    """
    _initialize_firebase()
    
    db = firestore.client()
    collection = db.collection(collection_name)
    
    query = collection.order_by('created_at', direction=firestore.Query.DESCENDING)
    if limit:
        query = query.limit(limit)
    
    docs = query.stream()
    
    models = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        models.append(data)
    
    logger.info(f"モデル一覧を取得: {collection_name} ({len(models)}件)")
    return models

