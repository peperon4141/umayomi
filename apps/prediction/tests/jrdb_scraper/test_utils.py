"""ユーティリティ関数のテスト"""

"""ユーティリティ関数のテスト"""

import pytest

from src.jrdb_scraper.utils.date_formatter import (
    create_date_from_ymd,
    format_date_iso,
    format_date_jrdb,
    format_year_2digit,
)
from src.jrdb_scraper.utils.record_key import generate_record_key, sanitize_record_key


class TestDateFormatter:
    """日付フォーマッターのテスト"""

    def test_create_date_from_ymd(self):
        """年、月、日からDateオブジェクトを作成"""
        date_obj = create_date_from_ymd(2024, 11, 2)
        assert date_obj.year == 2024
        assert date_obj.month == 11
        assert date_obj.day == 2

    def test_format_date_iso(self):
        """ISO形式の日付文字列を作成"""
        result = format_date_iso(2024, 11, 2)
        assert result == '2024-11-02'

    def test_format_date_iso_single_digit(self):
        """1桁の月・日"""
        result = format_date_iso(2024, 1, 5)
        assert result == '2024-01-05'

    def test_format_date_jrdb(self):
        """JRDB形式の日付文字列を作成"""
        result = format_date_jrdb(2024, 11, 2)
        assert result == '241102'

    def test_format_date_jrdb_single_digit(self):
        """1桁の月・日"""
        result = format_date_jrdb(2024, 1, 5)
        assert result == '240105'

    def test_format_year_2digit(self):
        """2桁の年文字列を作成"""
        result = format_year_2digit(2024)
        assert result == '24'

    def test_format_year_2digit_2000(self):
        """2000年の場合"""
        result = format_year_2digit(2000)
        assert result == '00'


class TestRecordKey:
    """レコードキー生成のテスト"""

    def test_generate_record_key_with_race_key(self):
        """レースキーがある場合"""
        record = {'レースキー': '202411020101', 'その他': 'value'}
        key = generate_record_key(record, 0)
        assert key == '202411020101'

    def test_generate_record_key_with_horse_id(self):
        """血統登録番号がある場合"""
        record = {'血統登録番号': '12345678', 'その他': 'value'}
        key = generate_record_key(record, 0)
        assert key == '12345678'

    def test_generate_record_key_with_index(self):
        """キーフィールドがない場合、インデックスを使用"""
        record = {'その他': 'value'}
        key = generate_record_key(record, 5)
        assert key == 'record_5'

    def test_sanitize_record_key(self):
        """レコードキーのサニタイズ"""
        key = sanitize_record_key('2024/11/02')
        assert key == '2024_11_02'

    def test_sanitize_record_key_with_spaces(self):
        """スペースを含むキー"""
        key = sanitize_record_key('race key 123')
        assert key == 'race_key_123'

