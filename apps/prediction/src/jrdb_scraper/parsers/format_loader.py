"""フォーマット定義ローダー
JSON形式のフォーマット定義を読み込む
"""

import json
import logging
from pathlib import Path
from typing import Optional

from ..entities.jrdb import JRDBDataType
from .format_parser import JRDBFormatDefinition

logger = logging.getLogger(__name__)

# フォーマット定義のキャッシュ
_format_cache: dict[JRDBDataType, Optional[JRDBFormatDefinition]] = {}


def get_formats_dir() -> Path:
    """フォーマット定義ディレクトリのパスを取得
    
    Returns:
        フォーマット定義ディレクトリのPath
    """
    # このファイルの場所から相対的にformatsディレクトリを取得
    current_file = Path(__file__)
    return current_file.parent.parent / 'formats'


def load_format_definition(dataType: JRDBDataType) -> Optional[JRDBFormatDefinition]:
    """データタイプからJSONファイルを読み込んでフォーマット定義を取得
    
    Args:
        dataType: データタイプ
    
    Returns:
        フォーマット定義、見つからない場合はNone
    """
    # キャッシュをチェック
    if dataType in _format_cache:
        return _format_cache[dataType]
    
    formats_dir = get_formats_dir()
    json_file = formats_dir / f'{dataType.value.lower()}.json'
    
    if not json_file.exists():
        logger.warning(f'フォーマット定義ファイルが見つかりません: {json_file}')
        _format_cache[dataType] = None
        return None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            format_data = json.load(f)
        
        # JSONデータをJRDBFormatDefinitionに変換
        format_def: JRDBFormatDefinition = {
            'dataType': format_data['dataType'],
            'description': format_data['description'],
            'recordLength': format_data['recordLength'],
            'encoding': format_data['encoding'],
            'lineEnding': format_data['lineEnding'],
            'fields': format_data['fields']
        }
        
        # オプショナルフィールド
        if 'specificationUrl' in format_data:
            format_def['specificationUrl'] = format_data['specificationUrl']
        if 'usageGuideUrl' in format_data:
            format_def['usageGuideUrl'] = format_data['usageGuideUrl']
        if 'sampleUrl' in format_data:
            format_def['sampleUrl'] = format_data['sampleUrl']
        if 'note' in format_data:
            format_def['note'] = format_data['note']
        
        _format_cache[dataType] = format_def
        return format_def
    
    except Exception as e:
        logger.error(f'フォーマット定義ファイルの読み込みに失敗: {json_file}', exc_info=e)
        _format_cache[dataType] = None
        return None


def get_format_definition(dataType: JRDBDataType) -> Optional[JRDBFormatDefinition]:
    """データタイプからフォーマット定義を取得（エイリアス）
    
    Args:
        dataType: データタイプ
    
    Returns:
        フォーマット定義、見つからない場合はNone
    """
    return load_format_definition(dataType)

