"""レースキー生成のテスト"""

"""レースキー生成のテスト"""

import pytest
from datetime import date

from src.jrdb_scraper.race_key_generator import generate_jrdb_data_file_url


class TestGenerateJRDBDataFileUrl:
    """generate_jrdb_data_file_url関数のテスト"""

    def test_generate_url_for_kyi(self):
        """KYIデータタイプのURL生成"""
        date_obj = date(2025, 11, 2)
        url = generate_jrdb_data_file_url('KYI', date_obj)
        assert 'KYI251102.lzh' in url
        assert 'https://jrdb.com/member/data/Kyi' in url

    def test_generate_url_for_bac(self):
        """BACデータタイプのURL生成"""
        date_obj = date(2024, 1, 15)
        url = generate_jrdb_data_file_url('BAC', date_obj)
        assert 'BAC240115.lzh' in url
        assert 'https://jrdb.com/member/data/Bac' in url

    def test_generate_url_invalid_data_type(self):
        """無効なデータタイプ"""
        date_obj = date(2024, 1, 1)
        with pytest.raises(ValueError, match='未定義のデータタイプ'):
            generate_jrdb_data_file_url('INVALID', date_obj)

    def test_generate_url_single_digit_month_day(self):
        """1桁の月・日"""
        date_obj = date(2024, 1, 5)
        url = generate_jrdb_data_file_url('KYI', date_obj)
        assert 'KYI240105.lzh' in url

