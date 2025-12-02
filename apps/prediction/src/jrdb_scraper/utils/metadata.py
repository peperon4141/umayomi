"""メタデータ作成ユーティリティ"""

from typing import Dict, Optional


def create_storage_metadata(
    fileName: str,
    sourceUrl: str,
    dataType: str,
    date: str
) -> Dict[str, str]:
    """Storage用のメタデータを作成
    
    Args:
        fileName: ファイル名
        sourceUrl: ソースURL
        dataType: データタイプ
        date: 日付（ISO形式）
    
    Returns:
        メタデータ辞書
    """
    return {
        'fileName': fileName,
        'sourceUrl': sourceUrl or '',
        'dataType': dataType,
        'date': date
    }


def create_firestore_metadata(
    dataType: str,
    date: str,
    year: int,
    month: int,
    day: int,
    lzhStoragePath: Optional[str],
    npzStoragePath: str,
    jsonStoragePath: str,
    fileName: str,
    recordCount: int
) -> Dict[str, any]:
    """Firestore用のメタデータを作成
    
    Args:
        dataType: データタイプ
        date: 日付（ISO形式）
        year: 年
        month: 月
        day: 日
        lzhStoragePath: LZHファイルのStorageパス
        npzStoragePath: NPZファイルのStorageパス
        jsonStoragePath: JSONファイルのStorageパス
        fileName: ファイル名
        recordCount: レコード数
    
    Returns:
        メタデータ辞書
    """
    from datetime import datetime
    
    return {
        'dataType': dataType,
        'date': date,
        'year': year,
        'month': month,
        'day': day,
        'lzhStoragePath': lzhStoragePath,
        'npzStoragePath': npzStoragePath,
        'jsonStoragePath': jsonStoragePath,
        'fileName': fileName,
        'recordCount': recordCount,
        'fetchedAt': datetime.now()
    }

