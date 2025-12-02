"""フォーマットパーサーのテスト"""

"""フォーマットパーサーのテスト"""

import pytest

from src.jrdb_scraper.parsers.format_parser import (
    JRDBFormatDefinition,
    parse_data_from_buffer,
    parse_record_from_buffer,
)


class TestParseRecordFromBuffer:
    """parse_record_from_buffer関数のテスト"""

    @pytest.fixture
    def sample_format(self):
        """サンプルフォーマット定義"""
        return {
            'dataType': 'TEST',
            'description': 'テストデータ',
            'recordLength': 20,
            'encoding': 'ShiftJIS',
            'lineEnding': 'CRLF',
            'fields': [
                {
                    'name': '場コード',
                    'start': 1,
                    'length': 2,
                    'type': 'integer_nine',
                    'description': '場コード'
                },
                {
                    'name': '年',
                    'start': 3,
                    'length': 2,
                    'type': 'integer_nine',
                    'description': '年'
                },
                {
                    'name': '名前',
                    'start': 5,
                    'length': 10,
                    'type': 'string',
                    'description': '名前'
                },
                {
                    'name': '数値',
                    'start': 15,
                    'length': 5,
                    'type': 'integer_zero_blank',
                    'description': '数値'
                }
            ]
        }

    def test_parse_record_basic(self, sample_format):
        """基本的なレコードパース"""
        # "01" + "24" + "テスト      " + "  123" (20バイト)
        # 場コード(2) + 年(2) + 名前(10) + 数値(5) + 予備(1) = 20バイト
        test_name = 'テスト'.encode('shift_jis')
        buffer = b'01' + b'24' + test_name + b' ' * (10 - len(test_name)) + b'  123'
        # 20バイトに満たない場合はパディング
        if len(buffer) < 20:
            buffer += b' ' * (20 - len(buffer))
        record = parse_record_from_buffer(buffer, sample_format)
        
        assert record['場コード'] == 1
        assert record['年'] == 24
        assert isinstance(record['名前'], str)
        # 数値フィールドは15バイト目から5バイト
        assert record['数値'] == 123

    def test_parse_record_with_empty_value(self, sample_format):
        """空の値が含まれるレコード"""
        buffer = b'0124\xe3\x83\x86\xe3\x82\xb9\xe3\x83\x88      ' + b'     '
        record = parse_record_from_buffer(buffer, sample_format)
        
        assert record['場コード'] == 1
        assert record['数値'] is None  # INTEGER_ZERO_BLANKで空文字列はNone


class TestParseDataFromBuffer:
    """parse_data_from_buffer関数のテスト"""

    @pytest.fixture
    def sample_format(self):
        """サンプルフォーマット定義"""
        return {
            'dataType': 'TEST',
            'description': 'テストデータ',
            'recordLength': 10,
            'encoding': 'ShiftJIS',
            'lineEnding': 'CRLF',
            'fields': [
                {
                    'name': '数値1',
                    'start': 1,
                    'length': 3,
                    'type': 'integer_nine',
                    'description': '数値1'
                },
                {
                    'name': '数値2',
                    'start': 4,
                    'length': 3,
                    'type': 'integer_nine',
                    'description': '数値2'
                },
                {
                    'name': '改行',
                    'start': 7,
                    'length': 2,
                    'type': 'string',
                    'description': '改行'
                }
            ]
        }

    def test_parse_multiple_records(self, sample_format):
        """複数レコードのパース"""
        # レコード長10バイトの固定長レコード
        # レコード1: "123456    " (10バイト) + CRLF
        # レコード2: "789012    " (10バイト) + CRLF
        buffer = b'123456    ' + b'\r\n' + b'789012    ' + b'\r\n'
        records = parse_data_from_buffer(buffer, sample_format)
        
        assert len(records) == 2
        assert records[0]['数値1'] == 123
        assert records[0]['数値2'] == 456
        assert records[1]['数値1'] == 789
        assert records[1]['数値2'] == 12

    def test_parse_with_lf_only(self, sample_format):
        """LFのみの改行コード"""
        # レコード長10バイトの固定長レコード
        # レコード1: "123456    " (10バイト) + LF
        # レコード2: "789012    " (10バイト) + LF
        buffer = b'123456    ' + b'\n' + b'789012    ' + b'\n'
        records = parse_data_from_buffer(buffer, sample_format)
        
        assert len(records) == 2
        assert records[0]['数値1'] == 123
        assert records[1]['数値1'] == 789

    def test_parse_incomplete_record(self, sample_format):
        """不完全なレコード（レコード長に満たない）"""
        buffer = b'123456\r\n789'  # 2レコード目が不完全
        records = parse_data_from_buffer(buffer, sample_format)
        
        # 完全なレコードのみがパースされる
        assert len(records) == 1
        assert records[0]['数値1'] == 123

