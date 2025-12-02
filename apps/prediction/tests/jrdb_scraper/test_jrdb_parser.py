"""JRDBパーサーのテスト"""

"""JRDBパーサーのテスト"""

import pytest

from src.jrdb_scraper.entities.jrdb import JRDBDataType
from src.jrdb_scraper.parsers.jrdb_parser import (
    find_jrdb_data_type,
    get_format_definition_from_string,
    parse_jrdb_file_name,
)


class TestFindJrdbDataType:
    """find_jrdb_data_type関数のテスト"""

    def test_find_valid_data_type(self):
        """有効なデータタイプ"""
        result = find_jrdb_data_type('KYI')
        assert result == JRDBDataType.KYI

    def test_find_case_insensitive(self):
        """大文字小文字を区別しない"""
        result = find_jrdb_data_type('kyi')
        assert result == JRDBDataType.KYI

    def test_find_invalid_data_type(self):
        """無効なデータタイプ"""
        result = find_jrdb_data_type('INVALID')
        assert result is None


class TestParseJrdbFileName:
    """parse_jrdb_file_name関数のテスト"""

    def test_parse_daily_file_name(self):
        """日単位ファイル名のパース"""
        result = parse_jrdb_file_name('KYI251102.lzh')
        assert result is not None
        assert result['dataType'] == JRDBDataType.KYI
        assert result['year'] == 2025
        assert result['month'] == 11
        assert result['day'] == 2

    def test_parse_annual_file_name(self):
        """年度パックファイル名のパース"""
        result = parse_jrdb_file_name('BAC_2024.lzh')
        assert result is not None
        assert result['dataType'] == JRDBDataType.BAC
        assert result['year'] == 2024
        assert 'month' not in result
        assert 'day' not in result

    def test_parse_txt_file_name(self):
        """TXTファイル名のパース"""
        result = parse_jrdb_file_name('KYG251102.txt')
        assert result is not None
        assert result['dataType'] == JRDBDataType.KYG

    def test_parse_invalid_file_name(self):
        """無効なファイル名"""
        result = parse_jrdb_file_name('invalid.txt')
        assert result is None

    def test_parse_invalid_format(self):
        """無効なフォーマット"""
        result = parse_jrdb_file_name('KYI.lzh')
        assert result is None


class TestGetFormatDefinitionFromString:
    """get_format_definition_from_string関数のテスト"""

    def test_get_valid_format(self):
        """有効なデータタイプからフォーマット定義を取得"""
        format_def = get_format_definition_from_string('KSA')
        assert format_def is not None
        assert format_def['dataType'] == 'KSA'
        assert 'fields' in format_def
        assert len(format_def['fields']) > 0

    def test_get_invalid_format(self):
        """無効なデータタイプ"""
        with pytest.raises(ValueError, match='未定義のデータタイプ'):
            get_format_definition_from_string('INVALID')

