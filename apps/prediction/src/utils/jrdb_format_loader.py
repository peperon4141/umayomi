"""JRDBフォーマット定義ローダー
apps/prediction/src/jrdb_scraper/formats のJSONファイルをロード
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, TypedDict

from src.jrdb_scraper.entities.jrdb import JRDBDataType

logger = logging.getLogger(__name__)


class JRDBFieldDefinition(TypedDict):
    """JRDBフィールド定義の型"""
    name: str
    start: int
    length: int
    type: str
    description: str


class JRDBFormatDefinition(TypedDict):
    """JRDBフォーマット定義の型"""
    dataType: str
    description: str
    recordLength: int
    encoding: str
    lineEnding: str
    identifierColumns: List[str]
    fields: List[JRDBFieldDefinition]


class JRDBFormatLoader:
    """JRDBフォーマット定義ローダー（apps/prediction/src/jrdb_scraper/formats のJSONファイルをロード）"""
    
    def __init__(self, formats_dir: Path):
        """フォーマット定義のキャッシュを初期化（formats_dir: フォーマット定義ディレクトリのパス）"""
        if formats_dir is None:
            raise ValueError('formats_dirは必須です')
        self._format_cache: Dict[JRDBDataType, Optional[JRDBFormatDefinition]] = {}
        self._formats_dir = Path(formats_dir)
    
    def load_format_definition(self, dataType: JRDBDataType) -> Optional[JRDBFormatDefinition]:
        """データタイプからJSONファイルを読み込んでフォーマット定義を取得（identifierColumns, raceKeyを含む）"""
        # キャッシュをチェック
        if dataType in self._format_cache:
            return self._format_cache[dataType]
        
        json_file = self._formats_dir / f'{dataType.value.lower()}.json'
        
        if not json_file.exists():
            logger.warning(f'フォーマット定義ファイルが見つかりません: {json_file}')
            self._format_cache[dataType] = None
            return None
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                format_data: Dict[str, Any] = json.load(f)
            
            # identifierColumnsは必須
            if 'identifierColumns' not in format_data:
                raise ValueError(f'identifierColumnsが必須ですが、{json_file}に含まれていません')
            
            # JRDBFormatDefinition型にキャスト
            format_def: JRDBFormatDefinition = {
                'dataType': format_data['dataType'],
                'description': format_data['description'],
                'recordLength': format_data['recordLength'],
                'encoding': format_data['encoding'],
                'lineEnding': format_data['lineEnding'],
                'identifierColumns': format_data['identifierColumns'],
                'fields': format_data['fields']
            }
            
            # キャッシュに保存
            self._format_cache[dataType] = format_def
            return format_def
        
        except Exception as e:
            logger.error(f'フォーマット定義ファイルの読み込みに失敗: {json_file}', exc_info=e)
            self._format_cache[dataType] = None
            return None
    
    



