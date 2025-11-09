/**
 * JRDBデータの型定義
 * JRDBデータは固定長テキスト形式で提供される
 */

/**
 * JRDBデータ種別
 * フォーマット定義ファイルと一致する詳細なデータ型のみ定義
 */
/* eslint-disable no-unused-vars */
export enum JRDBDataType {
  // KY系（競走馬データ）
  KYI = 'KYI', // 競走馬データ（牧場先情報付き）
  KYH = 'KYH', // 競走馬データ（標準版）
  KYG = 'KYG', // 競走馬データ（標準版）
  KKA = 'KKA', // 競走馬拡張データ（KY系）
  // BA系（番組データ）
  BAC = 'BAC', // 番組データ（BAC）
  BAB = 'BAB', // 番組データ（BAB）
  // O系（オッズデータ）
  OZ = 'OZ', // 基準オッズデータ（単複、馬連）
  OW = 'OW', // 基準オッズデータ（ワイド）
  OU = 'OU', // 基準馬単データ
  OT = 'OT', // 基準３連複データ
  OV = 'OV', // 基準３連単データ
  // HJ系（払戻情報データ）
  HJC = 'HJC', // 払戻情報データ（HJC）
  HJB = 'HJB', // 払戻情報データ（HJB）
  // SE系（成績データ）
  // 注意: SRBとSRAはSED/SECに同梱されているため、個別のデータタイプとして定義しない
  SED = 'SED', // 成績速報データ（SED）
  SEC = 'SEC', // 成績速報データ（SEC）
  // ZE系（前走データ）
  ZED = 'ZED', // 前走データ（ZED）
  ZEC = 'ZEC', // 前走データ（ZEC）
  // その他
  UKC = 'UKC', // 馬基本データ
  JOA = 'JOA', // 情報データ
  TYB = 'TYB', // 直前情報データ
  KZA = 'KZA', // 騎手データ（全騎手分）
  KSA = 'KSA', // 騎手データ（今週出走分）
  CZA = 'CZA', // 調教師データ（全調教師分）
  CSA = 'CSA' // 調教師データ（今週出走分）
}
/* eslint-enable no-unused-vars */

/**
 * JRDBデータの基本情報
 */
export interface JRDBDataInfo {
  dataType: JRDBDataType
  year: number
  encoding?: 'ShiftJIS' | 'UTF-8'
}

/**
 * JRDBデータタイプの情報
 */
export interface JRDBDataTypeInfo {
  /** データタイプ */
  dataType: JRDBDataType
  /** 仕様書URL */
  specificationUrl: string
  /** データファイルのベースURL */
  dataFileBaseUrl: string
  /** データファイルのディレクトリパス（URL生成用） */
  dataFileDirectory: string
}

/**
 * JRDBデータタイプごとの情報マップ
 */
export const JRDB_DATA_TYPE_INFO: Record<JRDBDataType, JRDBDataTypeInfo> = {
  // KY系（競走馬データ）
  [JRDBDataType.KYI]: {
    dataType: JRDBDataType.KYI,
    specificationUrl: 'https://jrdb.com/program/Kyi/kyi_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kyi',
    dataFileDirectory: 'Kyi'
  },
  [JRDBDataType.KYH]: {
    dataType: JRDBDataType.KYH,
    specificationUrl: 'https://jrdb.com/program/Kyh/kyh_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kyh',
    dataFileDirectory: 'Kyh'
  },
  [JRDBDataType.KYG]: {
    dataType: JRDBDataType.KYG,
    specificationUrl: 'https://jrdb.com/program/Kyg/kyg_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kyg',
    dataFileDirectory: 'Kyg'
  },
  [JRDBDataType.KKA]: {
    dataType: JRDBDataType.KKA,
    specificationUrl: 'https://jrdb.com/program/Kka/kka_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kka',
    dataFileDirectory: 'Kka'
  },
  
  // BA系（番組データ）
  [JRDBDataType.BAC]: {
    dataType: JRDBDataType.BAC,
    specificationUrl: 'https://jrdb.com/program/Bac/bac_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Bac',
    dataFileDirectory: 'Bac'
  },
  [JRDBDataType.BAB]: {
    dataType: JRDBDataType.BAB,
    specificationUrl: 'https://jrdb.com/program/Bab/bab_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Bab',
    dataFileDirectory: 'Bab'
  },
  
  // O系（オッズデータ）
  [JRDBDataType.OZ]: {
    dataType: JRDBDataType.OZ,
    specificationUrl: 'https://jrdb.com/program/Oz/Ozdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Oz',
    dataFileDirectory: 'Oz'
  },
  [JRDBDataType.OW]: {
    dataType: JRDBDataType.OW,
    specificationUrl: 'https://jrdb.com/program/Oz/Owdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Oz',
    dataFileDirectory: 'Oz'
  },
  [JRDBDataType.OU]: {
    dataType: JRDBDataType.OU,
    specificationUrl: 'https://jrdb.com/program/Ou/Oudata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ou',
    dataFileDirectory: 'Ou'
  },
  [JRDBDataType.OT]: {
    dataType: JRDBDataType.OT,
    specificationUrl: 'https://jrdb.com/program/Ot/Otdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ot',
    dataFileDirectory: 'Ot'
  },
  [JRDBDataType.OV]: {
    dataType: JRDBDataType.OV,
    specificationUrl: 'https://jrdb.com/program/Ov/ovdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ov',
    dataFileDirectory: 'Ov'
  },
  
  // HJ系（払戻情報データ）
  [JRDBDataType.HJC]: {
    dataType: JRDBDataType.HJC,
    specificationUrl: 'https://jrdb.com/program/Hjc/hjcdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Hjc',
    dataFileDirectory: 'Hjc'
  },
  [JRDBDataType.HJB]: {
    dataType: JRDBDataType.HJB,
    specificationUrl: 'https://jrdb.com/program/Hjb/hjb_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Hjb',
    dataFileDirectory: 'Hjb'
  },
  
  // SE系（成績データ）
  // 注意: SRBとSRAはSED/SECに同梱されているため、個別のデータタイプとして定義しない
  [JRDBDataType.SED]: {
    dataType: JRDBDataType.SED,
    specificationUrl: 'https://jrdb.com/program/Sed/sed_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Sed',
    dataFileDirectory: 'Sed'
  },
  [JRDBDataType.SEC]: {
    dataType: JRDBDataType.SEC,
    specificationUrl: 'https://jrdb.com/program/Sec/sec_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Sec',
    dataFileDirectory: 'Sec'
  },
  
  // ZE系（前走データ）- 成績データと同じフォーマット
  [JRDBDataType.ZED]: {
    dataType: JRDBDataType.ZED,
    specificationUrl: 'https://jrdb.com/program/Sed/sed_doc.txt', // ZEDはSEDと同じフォーマット
    dataFileBaseUrl: 'https://jrdb.com/member/data/Zed',
    dataFileDirectory: 'Zed'
  },
  [JRDBDataType.ZEC]: {
    dataType: JRDBDataType.ZEC,
    specificationUrl: 'https://jrdb.com/program/Sec/sec_doc.txt', // ZECはSECと同じフォーマット
    dataFileBaseUrl: 'https://jrdb.com/member/data/Zec',
    dataFileDirectory: 'Zec'
  },
  
  // その他
  [JRDBDataType.UKC]: {
    dataType: JRDBDataType.UKC,
    specificationUrl: 'https://jrdb.com/program/Ukc/ukc_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ukc',
    dataFileDirectory: 'Ukc'
  },
  [JRDBDataType.JOA]: {
    dataType: JRDBDataType.JOA,
    specificationUrl: 'https://jrdb.com/program/Jo/Jodata_doc2.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Jo',
    dataFileDirectory: 'Jo'
  },
  [JRDBDataType.TYB]: {
    dataType: JRDBDataType.TYB,
    specificationUrl: 'https://jrdb.com/program/Tyb/tyb_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Tyb',
    dataFileDirectory: 'Tyb'
  },
  
  // 騎手・調教師データ（日付付きで提供される）
  [JRDBDataType.KZA]: {
    dataType: JRDBDataType.KZA,
    specificationUrl: 'https://jrdb.com/program/Ks/Ks_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ks',
    dataFileDirectory: 'Ks'
  },
  [JRDBDataType.KSA]: {
    dataType: JRDBDataType.KSA,
    specificationUrl: 'https://jrdb.com/program/Ks/Ks_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ks',
    dataFileDirectory: 'Ks'
  },
  [JRDBDataType.CZA]: {
    dataType: JRDBDataType.CZA,
    specificationUrl: 'https://jrdb.com/program/Cs/Cs_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Cs',
    dataFileDirectory: 'Cs'
  },
  [JRDBDataType.CSA]: {
    dataType: JRDBDataType.CSA,
    specificationUrl: 'https://jrdb.com/program/Cs/Cs_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Cs',
    dataFileDirectory: 'Cs'
  }
}

/**
 * データタイプの情報を取得
 */
export function getJRDBDataTypeInfo(dataType: JRDBDataType): JRDBDataTypeInfo {
  return JRDB_DATA_TYPE_INFO[dataType]
}

/**
 * 仕様書URLを取得
 */
export function getSpecificationUrl(dataType: JRDBDataType): string {
  return JRDB_DATA_TYPE_INFO[dataType].specificationUrl
}

export function getAllDataTypes(): JRDBDataType[] {
  return Object.values(JRDBDataType)
}