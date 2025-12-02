"""JRDBフォーマットパーサー
レコード解析
"""

import logging
from typing import Dict, List, Optional, TypedDict, Union

from .field_parser import JRDBFieldType, extract_field_value_from_buffer

logger = logging.getLogger(__name__)


class JRDBFieldDefinition(TypedDict):
    """JRDBフィールド定義の型"""
    name: str
    start: int
    length: int
    type: str  # JRDBFieldTypeの文字列値
    description: str


class JRDBFormatDefinition(TypedDict, total=False):
    """JRDBフォーマット定義の型"""
    dataType: str
    description: str
    recordLength: int
    encoding: str
    lineEnding: str
    specificationUrl: Optional[str]
    usageGuideUrl: Optional[str]
    sampleUrl: Optional[str]
    fields: List[JRDBFieldDefinition]
    note: Optional[str]


def parse_data_from_buffer(buffer: bytes, format: JRDBFormatDefinition) -> List[Dict[str, Union[int, str, None]]]:
    """ShiftJISバッファからJRDBデータをパース（汎用関数）
    ShiftJISのバイト位置で正確にパースする
    
    Args:
        buffer: ShiftJISでエンコードされたバッファ
        format: フォーマット定義
    
    Returns:
        パースされたレコードの配列
    """
    logger.info('JRDBデータのパース開始（ShiftJISバッファ）', extra={
        'dataType': format['dataType'],
        'bufferLength': len(buffer)
    })
    
    records: List[Dict[str, Union[int, str, None]]] = []
    recordLength = format['recordLength']
    
    # 固定長レコードとして処理（改行コードに関係なく、recordLengthごとに切り出す）
    offset = 0
    lineNumber = 0
    
    while offset + recordLength <= len(buffer):
        # レコードを切り出す（recordLengthバイト）
        recordBuffer = buffer[offset:offset + recordLength]
        
        # レコード長が正確でない場合はスキップ
        if len(recordBuffer) != recordLength:
            logger.warning('Record buffer length mismatch', extra={
                'dataType': format['dataType'],
                'expectedLength': recordLength,
                'actualLength': len(recordBuffer),
                'lineNumber': lineNumber + 1
            })
            break
        
        offset += recordLength
        
        # 改行コードをスキップ（CRLFまたはLF）- レコードの後に改行がある場合
        if offset < len(buffer):
            if buffer[offset:offset + 2] == b'\x0D\x0A':  # CRLF
                offset += 2
            elif buffer[offset] == 0x0A:  # LF
                offset += 1
        
        try:
            record = parse_record_from_buffer(recordBuffer, format)
            records.append(record)
        except Exception as error:
            logger.error('JRDBレコードのパースに失敗', extra={
                'dataType': format['dataType'],
                'lineNumber': lineNumber + 1,
                'error': str(error)
            })
        
        lineNumber += 1
    
    logger.info('JRDBデータのパース完了（ShiftJISバッファ）', extra={
        'dataType': format['dataType'],
        'totalRecords': len(records)
    })
    
    return records


def parse_record_from_buffer(recordBuffer: bytes, format: JRDBFormatDefinition) -> Dict[str, Union[int, str, None]]:
    """ShiftJISバッファの1レコードを解析（バイト位置ベース）
    
    Args:
        recordBuffer: 1レコード分のバッファ
        format: フォーマット定義
    
    Returns:
        パースされたレコード（辞書）
    """
    record: Dict[str, Union[int, str, None]] = {}
    
    for field in format['fields']:
        value = extract_field_value_from_buffer(recordBuffer, field)
        record[field['name']] = value
    
    # KKAのレースキーの「日」フィールド（6バイト目）は16進数形式（TYPE F）
    # 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
    # 「日 1 F 6 16進数(日付 or 開催回数、日目)」
    # レースキー全体をパースした後、6バイト目（0ベースで5番目）の文字を16進数→10進数に変換
    if format['dataType'] == 'KKA' and 'レースキー' in record:
        raceKey = record['レースキー']
        if raceKey and isinstance(raceKey, str) and len(raceKey) >= 6:
            try:
                # 6バイト目（0ベースで5番目）の文字を16進数から10進数に変換
                hexChar = raceKey[5]
                decimalValue = int(hexChar, 16)
                if 0 <= decimalValue <= 15:
                    record['レースキー'] = raceKey[:5] + str(decimalValue) + raceKey[6:]
            except (ValueError, IndexError):
                # 変換失敗時は元の値を保持
                pass
    
    return record

