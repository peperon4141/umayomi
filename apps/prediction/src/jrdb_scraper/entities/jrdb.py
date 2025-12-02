"""JRDBデータの型定義
JRDBデータは固定長テキスト形式で提供される
"""

from enum import Enum
from typing import Dict, List, Optional, TypedDict


class JRDBDataType(str, Enum):
    """JRDBデータ種別
    フォーマット定義ファイルと一致する詳細なデータ型のみ定義
    """
    # KY系（競走馬データ）
    KYI = 'KYI'  # 競走馬データ（牧場先情報付き）
    KYH = 'KYH'  # 競走馬データ（標準版）
    KYG = 'KYG'  # 競走馬データ（標準版）
    KKA = 'KKA'  # 競走馬拡張データ（KY系）
    # BA系（番組データ）
    BAC = 'BAC'  # 番組データ（BAC）
    BAB = 'BAB'  # 番組データ（BAB）
    # KA系（開催データ）
    KAA = 'KAA'  # 開催データ（KAA）
    KAB = 'KAB'  # 開催データ（KAB）
    # KT系（登録馬データ）
    KTA = 'KTA'  # 登録馬データ（KTA）
    # O系（オッズデータ）
    OZ = 'OZ'  # 基準オッズデータ（単複、馬連）
    OW = 'OW'  # 基準オッズデータ（ワイド）
    OU = 'OU'  # 基準馬単データ
    OT = 'OT'  # 基準３連複データ
    OV = 'OV'  # 基準３連単データ
    # HJ系（払戻情報データ）
    HJC = 'HJC'  # 払戻情報データ（HJC）
    HJB = 'HJB'  # 払戻情報データ（HJB）
    # SE系（成績データ）
    # 注意: SRBとSRAはSED/SECに同梱されているため、個別のデータタイプとして定義しない
    SED = 'SED'  # 成績速報データ（SED）
    SEC = 'SEC'  # 成績速報データ（SEC）
    # ZE系（前走データ）
    ZED = 'ZED'  # 前走データ（ZED）
    ZEC = 'ZEC'  # 前走データ（ZEC）
    # その他
    UKC = 'UKC'  # 馬基本データ
    JOA = 'JOA'  # 情報データ
    TYB = 'TYB'  # 直前情報データ
    KZA = 'KZA'  # 騎手データ（全騎手分）
    KSA = 'KSA'  # 騎手データ（今週出走分）
    CZA = 'CZA'  # 調教師データ（全調教師分）
    CSA = 'CSA'  # 調教師データ（今週出走分）


class JRDBDataInfo(TypedDict, total=False):
    """JRDBデータの基本情報"""
    dataType: JRDBDataType
    year: int
    encoding: Optional[str]  # 'ShiftJIS' | 'UTF-8'


class JRDBDataTypeInfo(TypedDict):
    """JRDBデータタイプの情報"""
    dataType: JRDBDataType  # データタイプ
    description: str  # データタイプの説明
    specificationUrl: str  # 仕様書URL
    dataFileBaseUrl: str  # データファイルのベースURL
    dataFileDirectory: str  # データファイルのディレクトリパス（URL生成用）
    hasAnnualPack: bool  # 年度パックが提供されているか
    isMasterData: bool  # マスターデータかどうか（最新の週のデータにすべてのデータが含まれている）


# JRDBデータタイプごとの情報マップ
JRDB_DATA_TYPE_INFO: Dict[JRDBDataType, JRDBDataTypeInfo] = {
    # KY系（競走馬データ）- 日付単位で更新
    JRDBDataType.KYI: {
        'dataType': JRDBDataType.KYI,
        'description': '競走馬データ（牧場先情報付き・最も詳細）',
        'specificationUrl': 'https://jrdb.com/program/Kyi/kyi_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kyi',
        'dataFileDirectory': 'Kyi',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.KYH: {
        'dataType': JRDBDataType.KYH,
        'description': '競走馬データ（標準版）',
        'specificationUrl': 'https://jrdb.com/program/Kyh/kyh_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kyh',
        'dataFileDirectory': 'Kyh',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.KYG: {
        'dataType': JRDBDataType.KYG,
        'description': '競走馬データ（標準版・KYHと同形式）',
        'specificationUrl': 'https://jrdb.com/program/Kyg/kyg_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kyg',
        'dataFileDirectory': 'Kyg',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.KKA: {
        'dataType': JRDBDataType.KKA,
        'description': '競走馬拡張データ（KY系の詳細情報）',
        'specificationUrl': 'https://jrdb.com/program/Kka/kka_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kka',
        'dataFileDirectory': 'Kka',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    # BA系（番組データ）- 日付単位で更新
    JRDBDataType.BAC: {
        'dataType': JRDBDataType.BAC,
        'description': '番組データ（レース条件・出走馬一覧）',
        'specificationUrl': 'https://jrdb.com/program/Bac/bac_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Bac',
        'dataFileDirectory': 'Bac',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.BAB: {
        'dataType': JRDBDataType.BAB,
        'description': '番組データ（レース条件・出走馬一覧）',
        'specificationUrl': 'https://jrdb.com/program/Bab/bab_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Bab',
        'dataFileDirectory': 'Bab',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    # KA系（開催データ）- 日付単位で更新、年度パックなし
    JRDBDataType.KAA: {
        'dataType': JRDBDataType.KAA,
        'description': '開催データ（KAA）',
        'specificationUrl': 'https://jrdb.com/program/Kaa/kaa_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kaa',
        'dataFileDirectory': 'Kaa',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.KAB: {
        'dataType': JRDBDataType.KAB,
        'description': '開催データ（KAB）',
        'specificationUrl': 'https://jrdb.com/program/Kab/kab_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kab',
        'dataFileDirectory': 'Kab',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    # KT系（登録馬データ）- 日付単位で更新、年度パックなし
    JRDBDataType.KTA: {
        'dataType': JRDBDataType.KTA,
        'description': '登録馬データ（KTA）',
        'specificationUrl': 'https://jrdb.com/program/Kta/kta_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Kta',
        'dataFileDirectory': 'Kta',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    # O系（オッズデータ）- 日付単位で更新、年度パックなし
    JRDBDataType.OZ: {
        'dataType': JRDBDataType.OZ,
        'description': '基準オッズデータ（単複・馬連）',
        'specificationUrl': 'https://jrdb.com/program/Oz/Ozdata_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Oz',
        'dataFileDirectory': 'Oz',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.OW: {
        'dataType': JRDBDataType.OW,
        'description': '基準オッズデータ（ワイド）',
        'specificationUrl': 'https://jrdb.com/program/Oz/Owdata_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Oz',
        'dataFileDirectory': 'Oz',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.OU: {
        'dataType': JRDBDataType.OU,
        'description': '基準馬単データ',
        'specificationUrl': 'https://jrdb.com/program/Ou/Oudata_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Ou',
        'dataFileDirectory': 'Ou',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.OT: {
        'dataType': JRDBDataType.OT,
        'description': '基準３連複データ',
        'specificationUrl': 'https://jrdb.com/program/Ot/Otdata_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Ot',
        'dataFileDirectory': 'Ot',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.OV: {
        'dataType': JRDBDataType.OV,
        'description': '基準３連単データ',
        'specificationUrl': 'https://jrdb.com/program/Ov/ovdata_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Ov',
        'dataFileDirectory': 'Ov',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    # HJ系（払戻情報データ）- 日付単位で更新
    JRDBDataType.HJC: {
        'dataType': JRDBDataType.HJC,
        'description': '払戻情報データ（レース結果・払戻金）',
        'specificationUrl': 'https://jrdb.com/program/Hjc/hjcdata_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Hjc',
        'dataFileDirectory': 'Hjc',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.HJB: {
        'dataType': JRDBDataType.HJB,
        'description': '払戻情報データ（レース結果・払戻金）',
        'specificationUrl': 'https://jrdb.com/program/Hjb/hjb_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Hjb',
        'dataFileDirectory': 'Hjb',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    # SE系（成績データ）- 日付単位で更新、年度パックあり
    # 注意: SRBとSRAはSED/SECに同梱されているため、個別のデータタイプとして定義しない
    JRDBDataType.SED: {
        'dataType': JRDBDataType.SED,
        'description': '成績速報データ（レース結果詳細）',
        'specificationUrl': 'https://jrdb.com/program/Sed/sed_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Sed',
        'dataFileDirectory': 'Sed',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.SEC: {
        'dataType': JRDBDataType.SEC,
        'description': '成績速報データ（レース結果詳細）',
        'specificationUrl': 'https://jrdb.com/program/Sec/sec_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Sec',
        'dataFileDirectory': 'Sec',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    # ZE系（前走データ）- 成績データと同じフォーマット、年度パックなし
    JRDBDataType.ZED: {
        'dataType': JRDBDataType.ZED,
        'description': '前走データ（過去5走の成績・予測に必須）',
        'specificationUrl': 'https://jrdb.com/program/Sed/sed_doc.txt',  # ZEDはSEDと同じフォーマット
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Zed',
        'dataFileDirectory': 'Zed',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.ZEC: {
        'dataType': JRDBDataType.ZEC,
        'description': '前走データ（過去5走の成績・予測に必須）',
        'specificationUrl': 'https://jrdb.com/program/Sec/sec_doc.txt',  # ZECはSECと同じフォーマット
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Zec',
        'dataFileDirectory': 'Zec',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    # その他 - 日付単位で更新
    JRDBDataType.UKC: {
        'dataType': JRDBDataType.UKC,
        'description': '馬基本データ（血統登録番号・性別・生年月日・血統情報）',
        'specificationUrl': 'https://jrdb.com/program/Ukc/ukc_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Ukc',
        'dataFileDirectory': 'Ukc',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    JRDBDataType.JOA: {
        'dataType': JRDBDataType.JOA,
        'description': '情報データ（詳細情報による予想精度向上）',
        'specificationUrl': 'https://jrdb.com/program/Jo/Jodata_doc2.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Jo',
        'dataFileDirectory': 'Jo',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.TYB: {
        'dataType': JRDBDataType.TYB,
        'description': '直前情報データ（出走直前の馬の状態・当日予想に最重要）',
        'specificationUrl': 'https://jrdb.com/program/Tyb/tyb_doc.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Tyb',
        'dataFileDirectory': 'Tyb',
        'hasAnnualPack': True,
        'isMasterData': False
    },
    # 騎手・調教師データ（週単位で更新）- 年度パックなし、マスターデータ
    JRDBDataType.KZA: {
        'dataType': JRDBDataType.KZA,
        'description': '騎手データ（全騎手分・勝率・連対率・予測に必須）',
        'specificationUrl': 'https://jrdb.com/program/Ks/Ks_doc1.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Ks',
        'dataFileDirectory': 'Ks',
        'hasAnnualPack': False,
        'isMasterData': True
    },
    JRDBDataType.KSA: {
        'dataType': JRDBDataType.KSA,
        'description': '騎手データ（今週出走分・勝率・連対率・予測に必須）',
        'specificationUrl': 'https://jrdb.com/program/Ks/Ks_doc1.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Ks',
        'dataFileDirectory': 'Ks',
        'hasAnnualPack': False,
        'isMasterData': False
    },
    JRDBDataType.CZA: {
        'dataType': JRDBDataType.CZA,
        'description': '調教師データ（全調教師分・勝率・連対率・予測に必須）',
        'specificationUrl': 'https://jrdb.com/program/Cs/Cs_doc1.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Cs',
        'dataFileDirectory': 'Cs',
        'hasAnnualPack': False,
        'isMasterData': True
    },
    JRDBDataType.CSA: {
        'dataType': JRDBDataType.CSA,
        'description': '調教師データ（今週出走分・勝率・連対率・予測に必須）',
        'specificationUrl': 'https://jrdb.com/program/Cs/Cs_doc1.txt',
        'dataFileBaseUrl': 'https://jrdb.com/member/data/Cs',
        'dataFileDirectory': 'Cs',
        'hasAnnualPack': False,
        'isMasterData': False
    }
}


def get_jrdb_data_type_info(dataType: JRDBDataType) -> JRDBDataTypeInfo:
    """データタイプの情報を取得"""
    return JRDB_DATA_TYPE_INFO[dataType]


def get_specification_url(dataType: JRDBDataType) -> str:
    """仕様書URLを取得"""
    return JRDB_DATA_TYPE_INFO[dataType]['specificationUrl']


def generate_annual_pack_url(dataType: JRDBDataType, year: int) -> str:
    """年度パックのURLを生成
    
    Args:
        dataType: データタイプ
        year: 年度（例: 2024）
    
    Returns:
        年度パックのURL（例: `https://jrdb.com/member/data/Tyb/TYB_2024.lzh`）
    
    Raises:
        ValueError: 年度パックが提供されていないデータタイプの場合
    """
    info = JRDB_DATA_TYPE_INFO[dataType]
    if not info['hasAnnualPack']:
        raise ValueError(f'データタイプ {dataType} には年度パックが提供されていません')
    # 年度パックのファイル名形式: {DATA_TYPE}_{YEAR}.lzh（アンダースコアあり）
    # 例: BAC_2024.lzh, BAB_2024.lzh, KYI_2024.lzh
    fileName = f'{dataType}_{year}.lzh'
    # dataFileBaseUrlは既にディレクトリを含んでいる（例: https://jrdb.com/member/data/Bac）
    # ファイル名を直接追加（例: https://jrdb.com/member/data/Bac/BAC_2024.lzh）
    return f"{info['dataFileBaseUrl']}/{fileName}"


def get_all_data_types() -> List[JRDBDataType]:
    """すべてのデータタイプを取得"""
    return list(JRDBDataType)


def get_annual_pack_supported_data_types(dataTypes: List[JRDBDataType]) -> List[JRDBDataType]:
    """年度パックをサポートしているデータタイプのみをフィルタリング"""
    return [dt for dt in dataTypes if JRDB_DATA_TYPE_INFO[dt]['hasAnnualPack']]

