"""レコードキー生成ユーティリティ"""

from typing import Dict, Union


def generate_record_key(record: Dict[str, Union[int, str, None]], index: int) -> str:
    """レコードからFirestoreのドキュメントIDとして使用可能なキーを生成
    
    Args:
        record: レコード（辞書）
        index: インデックス
    
    Returns:
        レコードキー（文字列）
    """
    keyFields = [
        'レースキー',
        '血統登録番号',
        '競走成績キー',
        '騎手コード',
        '調教師コード',
        'レース番号',
        '日付'
    ]
    
    for field in keyFields:
        value = record.get(field)
        if value and isinstance(value, str) and value.strip():
            return sanitize_record_key(value)
    
    return f'record_{index}'


def sanitize_record_key(key: str) -> str:
    """レコードキーをFirestoreのドキュメントIDとして使用可能な形式に変換
    
    Args:
        key: レコードキー
    
    Returns:
        サニタイズされたレコードキー
    """
    import re
    return re.sub(r'[/\s]', '_', str(key))

