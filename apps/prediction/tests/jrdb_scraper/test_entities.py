"""エンティティのテスト"""

"""エンティティのテスト"""

import pytest

from src.jrdb_scraper.entities.code_tables import convert_keito_code_to_name, KEITO_CODE_MAP
from src.jrdb_scraper.entities.jrdb import (
    JRDBDataType,
    generate_annual_pack_url,
    get_all_data_types,
    get_annual_pack_supported_data_types,
    get_jrdb_data_type_info,
)
from src.jrdb_scraper.entities.venue import convert_racecourse_to_jrdb_venue_code, JRDB_VENUE_CODE_MAP


class TestJRDBDataType:
    """JRDBDataType Enumのテスト"""

    def test_data_type_values(self):
        """データタイプの値確認"""
        assert JRDBDataType.KYI.value == 'KYI'
        assert JRDBDataType.BAC.value == 'BAC'
        assert JRDBDataType.KSA.value == 'KSA'

    def test_all_data_types(self):
        """すべてのデータタイプを取得"""
        all_types = get_all_data_types()
        assert len(all_types) > 0
        assert JRDBDataType.KYI in all_types
        assert JRDBDataType.BAC in all_types


class TestGetJRDBDataTypeInfo:
    """get_jrdb_data_type_info関数のテスト"""

    def test_get_kyi_info(self):
        """KYIの情報取得"""
        info = get_jrdb_data_type_info(JRDBDataType.KYI)
        assert info['dataType'] == JRDBDataType.KYI
        assert info['hasAnnualPack'] is True
        assert 'specificationUrl' in info
        assert 'dataFileBaseUrl' in info

    def test_get_ksa_info(self):
        """KSAの情報取得"""
        info = get_jrdb_data_type_info(JRDBDataType.KSA)
        assert info['dataType'] == JRDBDataType.KSA
        assert info['hasAnnualPack'] is False
        assert info['isMasterData'] is False


class TestGenerateAnnualPackUrl:
    """generate_annual_pack_url関数のテスト"""

    def test_generate_annual_pack_url_supported(self):
        """年度パックをサポートしているデータタイプ"""
        url = generate_annual_pack_url(JRDBDataType.KYI, 2024)
        assert 'KYI_2024.lzh' in url
        assert 'https://jrdb.com/member/data' in url

    def test_generate_annual_pack_url_unsupported(self):
        """年度パックをサポートしていないデータタイプ"""
        with pytest.raises(ValueError, match='年度パックが提供されていません'):
            generate_annual_pack_url(JRDBDataType.KSA, 2024)


class TestGetAnnualPackSupportedDataTypes:
    """get_annual_pack_supported_data_types関数のテスト"""

    def test_filter_supported_types(self):
        """年度パックをサポートしているデータタイプのみをフィルタリング"""
        all_types = [JRDBDataType.KYI, JRDBDataType.KSA, JRDBDataType.BAC]
        supported = get_annual_pack_supported_data_types(all_types)
        
        assert JRDBDataType.KYI in supported
        assert JRDBDataType.BAC in supported
        assert JRDBDataType.KSA not in supported


class TestVenueCode:
    """競馬場コードのテスト"""

    def test_convert_racecourse_to_code(self):
        """競馬場名をコードに変換"""
        code = convert_racecourse_to_jrdb_venue_code('東京')
        assert code == '01'

    def test_convert_invalid_racecourse(self):
        """無効な競馬場名"""
        with pytest.raises(ValueError, match='Unknown racecourse'):
            convert_racecourse_to_jrdb_venue_code('無効な競馬場')

    def test_venue_code_map_completeness(self):
        """競馬場コードマップの完全性確認"""
        assert len(JRDB_VENUE_CODE_MAP) > 0
        assert '東京' in JRDB_VENUE_CODE_MAP
        assert '中山' in JRDB_VENUE_CODE_MAP


class TestKeitoCode:
    """系統コードのテスト"""

    def test_convert_keito_code(self):
        """系統コードを系統名に変換"""
        name = convert_keito_code_to_name('1101')
        assert name == 'ノーザンダンサー系'

    def test_convert_invalid_keito_code(self):
        """無効な系統コード"""
        with pytest.raises(ValueError, match='Unknown keito code'):
            convert_keito_code_to_name('9999')

    def test_keito_code_map_completeness(self):
        """系統コードマップの完全性確認"""
        assert len(KEITO_CODE_MAP) > 0
        assert '1101' in KEITO_CODE_MAP
        assert '1103' in KEITO_CODE_MAP

