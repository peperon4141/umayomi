"""フォーマットローダーのテスト"""

"""フォーマットローダーのテスト"""

import pytest

from src.jrdb_scraper.entities.jrdb import JRDBDataType
from src.jrdb_scraper.parsers.format_loader import load_format_definition


class TestLoadFormatDefinition:
    """load_format_definition関数のテスト"""

    def test_load_ksa_format(self):
        """KSAフォーマットの読み込み"""
        format_def = load_format_definition(JRDBDataType.KSA)
        assert format_def is not None
        assert format_def['dataType'] == 'KSA'
        assert format_def['recordLength'] == 272
        assert format_def['encoding'] == 'ShiftJIS'
        assert format_def['lineEnding'] == 'CRLF'
        assert len(format_def['fields']) > 0

    def test_load_kyi_format(self):
        """KYIフォーマットの読み込み"""
        format_def = load_format_definition(JRDBDataType.KYI)
        assert format_def is not None
        assert format_def['dataType'] == 'KYI'
        assert format_def['recordLength'] == 1024
        assert len(format_def['fields']) > 0

    def test_load_bac_format(self):
        """BACフォーマットの読み込み"""
        format_def = load_format_definition(JRDBDataType.BAC)
        assert format_def is not None
        assert format_def['dataType'] == 'BAC'
        assert format_def['recordLength'] == 184
        assert len(format_def['fields']) > 0

    def test_format_fields_structure(self):
        """フィールドの構造確認"""
        format_def = load_format_definition(JRDBDataType.KSA)
        assert format_def is not None
        
        # 最初のフィールドを確認
        first_field = format_def['fields'][0]
        assert 'name' in first_field
        assert 'start' in first_field
        assert 'length' in first_field
        assert 'type' in first_field
        assert 'description' in first_field

    def test_format_caching(self):
        """フォーマット定義のキャッシュ確認"""
        format_def1 = load_format_definition(JRDBDataType.KSA)
        format_def2 = load_format_definition(JRDBDataType.KSA)
        
        # 同じオブジェクトが返される（キャッシュされている）
        assert format_def1 is format_def2

