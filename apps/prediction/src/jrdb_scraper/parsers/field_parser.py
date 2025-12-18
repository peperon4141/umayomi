"""JRDBフィールドパーサー
ShiftJIS→UTF-8変換、型変換
"""

import codecs
from enum import Enum
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from .format_parser import JRDBFieldDefinition


class JRDBFieldType(str, Enum):
    """JRDBフィールドの型種別
    JRDB仕様書のTYPE（9/Z/X/F）に基づく
    - 9: 数字 (0のとき0)
    - Z: 数字（0のとき空白）
    - X: 文字
    - F: 16進数(数字 or 小文字アルファベット)
    """
    # 9型: 数字 (0のとき0)
    INTEGER_NINE = 'integer_nine'
    # Z型: 数字（0のとき空白）
    INTEGER_ZERO_BLANK = 'integer_zero_blank'
    # X型: 文字
    STRING = 'string'
    # F型: 16進数(数字 or 小文字アルファベット)
    STRING_HEX = 'string_hex'


def extract_field_value_from_buffer(buffer: bytes, field: 'JRDBFieldDefinition') -> Optional[Union[int, str]]:
    """ShiftJISバッファから指定位置・長さで値を抽出（バイト位置ベース）
    仕様書に基づいて、ShiftJISバッファからバイト位置で分割してからUTF-8に変換する
    
    Args:
        buffer: ShiftJISでエンコードされたバッファ
        field: フィールド定義
    
    Returns:
        抽出された値（int, str, None）
    """
    startIndex = field['start'] - 1  # 1ベースから0ベースに変換（仕様書は1ベース）
    endIndex = startIndex + field['length']
    
    if startIndex < 0 or endIndex > len(buffer):
        return None
    
    # ShiftJISバッファからバイト位置でフィールドを抽出（仕様書に基づく分割）
    fieldBuffer = buffer[startIndex:endIndex]
    
    # バッファが空の場合はnullを返す
    if len(fieldBuffer) == 0:
        return None
    
    # 抽出したバイト列をShiftJISからUTF-8に変換
    try:
        rawValue = codecs.decode(fieldBuffer, 'shift_jis').strip()
    except (UnicodeDecodeError, LookupError):
        # ShiftJIS変換に失敗した場合、ASCIIとして解釈を試みる
        rawValue = ''.join(
            chr(b) if 0x20 <= b <= 0x7E else ''
            for b in fieldBuffer
        ).strip()
    
    # KKAのレースキーの「日」フィールド（6バイト目、1バイト）は16進数形式
    # 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
    # 「日 1 F 6 16進数(日付 or 開催回数、日目)」
    # 16進数文字列を10進数に変換する必要がある
    if field['name'] == 'レースキー' and field['start'] == 6 and field['length'] == 1:
        # 16進数として解釈して10進数に変換
        try:
            hexValue = int(rawValue, 16)
            rawValue = str(hexValue)
        except (ValueError, TypeError):
            # 変換失敗時は元の値を保持
            pass
    
    # JRDB TYPEに応じた処理
    return convert_field_value(rawValue, field['type'])


def extract_field_value(line: str, field: 'JRDBFieldDefinition') -> Optional[Union[int, str]]:
    """固定長テキストから指定位置・長さで値を抽出（UTF-8文字列用、後方互換性のため保持）
    
    Args:
        line: UTF-8文字列
        field: フィールド定義
    
    Returns:
        抽出された値（int, str, None）
    """
    startIndex = field['start'] - 1  # 1ベースから0ベースに変換
    endIndex = startIndex + field['length']
    rawValue = line[startIndex:endIndex].strip()
    
    # JRDB TYPEに応じた処理
    return convert_field_value(rawValue, field['type'])


def convert_field_value(rawValue: str, fieldType: JRDBFieldType) -> Optional[Union[int, str]]:
    """フィールドの生値を型に応じて変換
    
    Args:
        rawValue: 生の文字列値
        fieldType: フィールドタイプ
    
    Returns:
        変換された値（int, str, None）
    """
    # INTEGER_ZERO_BLANK (Z型)の場合、空文字列はnull（0のとき空白）
    # 注意: Z型は「0のとき空白」という意味なので、0という値自体は有効
    if fieldType == JRDBFieldType.INTEGER_ZERO_BLANK:
        if rawValue == '' or rawValue.strip() == '':
            return None
        try:
            intValue = int(rawValue, 10)
            return intValue  # 0も有効な値として返す
        except (ValueError, TypeError):
            return None
    
    # INTEGER_NINE (9型)の場合
    if fieldType == JRDBFieldType.INTEGER_NINE:
        if rawValue == '' or rawValue.strip() == '':
            return None
        try:
            intValue = int(rawValue, 10)
            return intValue  # 0も有効な値
        except (ValueError, TypeError):
            return None
    
    # STRING, STRING_HEX型の場合
    return rawValue

