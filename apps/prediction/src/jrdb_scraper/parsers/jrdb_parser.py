"""JRDBパーサー
データタイプからフォーマット取得、ファイル名解析
"""

import logging
from typing import Dict, List, Optional, Union

from ..entities.jrdb import JRDBDataType
from .format_parser import JRDBFormatDefinition, parse_data_from_buffer
from .format_loader import load_format_definition

logger = logging.getLogger(__name__)


def get_format_definition_from_string(dataType: str) -> Optional[JRDBFormatDefinition]:
    """データタイプ文字列からフォーマット定義を取得
    
    Args:
        dataType: データタイプ文字列（例: "KYI", "BAC"）
    
    Returns:
        フォーマット定義、見つからない場合はNone
    
    Raises:
        ValueError: 未定義のデータタイプの場合
    """
    try:
        enumValue = JRDBDataType(dataType.upper())
    except ValueError:
        raise ValueError(f'未定義のデータタイプです: {dataType}')
    
    return load_format_definition(enumValue)


def parse_jrdb_file_name(fileName: str) -> Optional[Dict[str, Union[JRDBDataType, int]]]:
    """ファイル名からコードと日付を解析
    
    Args:
        fileName: ファイル名（例: "KYG251102.lzh", "KYI251102.lzh", "BAB_2024.lzh"）
    
    Returns:
        コードと日付情報、解析に失敗した場合はNone
    """
    import re
    
    # 汎用的なパターン: アルファベット + (オプションの区切り文字) + 数字(4-6桁) + 拡張子
    # 例: KYI251102.lzh, BAB_2024.lzh, KYG251102.txt
    match = re.match(r'^([A-Z]+)_?(\d{4,6})\.(lzh|txt)$', fileName, re.IGNORECASE)
    if not match or not match.group(1) or not match.group(2):
        return None
    
    dataType = find_jrdb_data_type(match.group(1).upper())
    if not dataType:
        return None
    
    dateStr = match.group(2)
    result: Dict[str, Union[JRDBDataType, int]] = {'dataType': dataType}
    
    # 6桁の場合はYYMMDD形式として解析
    if len(dateStr) == 6:
        try:
            year = int('20' + dateStr[:2])
            month = int(dateStr[2:4])
            day = int(dateStr[4:6])
            result['year'] = year
            result['month'] = month
            result['day'] = day
            return result
        except ValueError:
            pass
    
    # 4桁の場合は年のみとして解析
    if len(dateStr) == 4:
        try:
            year = int(dateStr)
            result['year'] = year
            return result
        except ValueError:
            pass
    
    return None


def find_jrdb_data_type(dataType: str) -> Optional[JRDBDataType]:
    """文字列からJRDBDataTypeに変換
    
    Args:
        dataType: データ型コード文字列
    
    Returns:
        マッチするJRDBDataType、見つからない場合はNone
    """
    try:
        return JRDBDataType(dataType.upper())
    except ValueError:
        return None


def parse_jrdb_data_from_buffer(
    buffer: bytes,
    dataType: Union[JRDBDataType, str]
) -> List[Dict[str, Union[int, str, None]]]:
    """JRDBデータをパース（汎用関数）
    
    Args:
        buffer: ShiftJISでエンコードされたバッファ
        dataType: データ種別（enumまたは文字列）
    
    Returns:
        パースされたレコードの配列
    """
    format: Optional[JRDBFormatDefinition] = None
    
    if isinstance(dataType, str):
        format = get_format_definition_from_string(dataType)
    else:
        format = load_format_definition(dataType)
    
    if not format:
        logger.warning('対応していないデータ種別です', extra={'dataType': dataType})
        return []
    
    return parse_data_from_buffer(buffer, format)

