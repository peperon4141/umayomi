"""フィールドパーサーのテスト"""

import pytest

from src.jrdb_scraper.parsers.field_parser import (
    JRDBFieldType,
    convert_field_value,
    extract_field_value_from_buffer,
)
from src.jrdb_scraper.parsers.format_parser import JRDBFieldDefinition


class TestConvertFieldValue:
    """convert_field_value関数のテスト"""

    def test_integer_nine_with_zero(self):
        """INTEGER_NINE型で0の値"""
        result = convert_field_value('0', JRDBFieldType.INTEGER_NINE)
        assert result == 0

    def test_integer_nine_with_number(self):
        """INTEGER_NINE型で数値"""
        result = convert_field_value('123', JRDBFieldType.INTEGER_NINE)
        assert result == 123

    def test_integer_nine_with_invalid(self):
        """INTEGER_NINE型で無効な値"""
        result = convert_field_value('abc', JRDBFieldType.INTEGER_NINE)
        assert result is None

    def test_integer_zero_blank_with_empty(self):
        """INTEGER_ZERO_BLANK型で空文字列"""
        result = convert_field_value('', JRDBFieldType.INTEGER_ZERO_BLANK)
        assert result is None

    def test_integer_zero_blank_with_zero(self):
        """INTEGER_ZERO_BLANK型で0"""
        result = convert_field_value('0', JRDBFieldType.INTEGER_ZERO_BLANK)
        assert result is None

    def test_integer_zero_blank_with_number(self):
        """INTEGER_ZERO_BLANK型で数値"""
        result = convert_field_value('123', JRDBFieldType.INTEGER_ZERO_BLANK)
        assert result == 123

    def test_string_type(self):
        """STRING型"""
        result = convert_field_value('test', JRDBFieldType.STRING)
        assert result == 'test'

    def test_string_hex_type(self):
        """STRING_HEX型"""
        result = convert_field_value('abc123', JRDBFieldType.STRING_HEX)
        assert result == 'abc123'


class TestExtractFieldValueFromBuffer:
    """extract_field_value_from_buffer関数のテスト"""

    @pytest.fixture
    def sample_buffer(self):
        """サンプルバッファ（ShiftJISエンコード）"""
        # "テスト123" をShiftJISでエンコード
        test_str = 'テスト123'
        return test_str.encode('shift_jis')

    def test_extract_string_field(self, sample_buffer):
        """文字列フィールドの抽出"""
        field: JRDBFieldDefinition = {
            'name': 'テスト',
            'start': 1,
            'length': 9,  # ShiftJISで「テスト」は6バイト
            'type': 'string',
            'description': 'テストフィールド'
        }
        result = extract_field_value_from_buffer(sample_buffer, field)
        assert isinstance(result, str)
        assert 'テスト' in result or result == 'テスト123'

    def test_extract_integer_field(self):
        """数値フィールドの抽出"""
        buffer = b'12345'
        field: JRDBFieldDefinition = {
            'name': '数値',
            'start': 1,
            'length': 3,
            'type': 'integer_nine',
            'description': '数値フィールド'
        }
        result = extract_field_value_from_buffer(buffer, field)
        assert result == 123

    def test_extract_out_of_range(self):
        """範囲外のフィールド"""
        buffer = b'123'
        field: JRDBFieldDefinition = {
            'name': '範囲外',
            'start': 10,
            'length': 5,
            'type': 'string',
            'description': '範囲外フィールド'
        }
        result = extract_field_value_from_buffer(buffer, field)
        assert result is None

    def test_extract_empty_buffer(self):
        """空のバッファ"""
        buffer = b''
        field: JRDBFieldDefinition = {
            'name': '空',
            'start': 1,
            'length': 1,
            'type': 'string',
            'description': '空フィールド'
        }
        result = extract_field_value_from_buffer(buffer, field)
        assert result is None

