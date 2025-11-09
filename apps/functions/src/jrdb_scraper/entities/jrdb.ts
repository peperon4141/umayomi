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
  /** データタイプの説明 */
  description: string
  /** 仕様書URL */
  specificationUrl: string
  /** データファイルのベースURL */
  dataFileBaseUrl: string
  /** データファイルのディレクトリパス（URL生成用） */
  dataFileDirectory: string
  /** 年度パックが提供されているか */
  hasAnnualPack: boolean
  /** マスターデータかどうか（最新の週のデータにすべてのデータが含まれている） */
  isMasterData: boolean
}

/**
 * JRDBデータタイプごとの情報マップ
 */
export const JRDB_DATA_TYPE_INFO: Record<JRDBDataType, JRDBDataTypeInfo> = {
  // KY系（競走馬データ）- 日付単位で更新
  [JRDBDataType.KYI]: {
    dataType: JRDBDataType.KYI,
    description: '競走馬データ（牧場先情報付き・最も詳細）',
    specificationUrl: 'https://jrdb.com/program/Kyi/kyi_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kyi',
    dataFileDirectory: 'Kyi',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.KYH]: {
    dataType: JRDBDataType.KYH,
    description: '競走馬データ（標準版）',
    specificationUrl: 'https://jrdb.com/program/Kyh/kyh_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kyh',
    dataFileDirectory: 'Kyh',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.KYG]: {
    dataType: JRDBDataType.KYG,
    description: '競走馬データ（標準版・KYHと同形式）',
    specificationUrl: 'https://jrdb.com/program/Kyg/kyg_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kyg',
    dataFileDirectory: 'Kyg',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.KKA]: {
    dataType: JRDBDataType.KKA,
    description: '競走馬拡張データ（KY系の詳細情報）',
    specificationUrl: 'https://jrdb.com/program/Kka/kka_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Kka',
    dataFileDirectory: 'Kka',
    hasAnnualPack: false,
    isMasterData: false
  },
  
  // BA系（番組データ）- 日付単位で更新
  [JRDBDataType.BAC]: {
    dataType: JRDBDataType.BAC,
    description: '番組データ（レース条件・出走馬一覧）',
    specificationUrl: 'https://jrdb.com/program/Bac/bac_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Bac',
    dataFileDirectory: 'Bac',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.BAB]: {
    dataType: JRDBDataType.BAB,
    description: '番組データ（レース条件・出走馬一覧）',
    specificationUrl: 'https://jrdb.com/program/Bab/bab_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Bab',
    dataFileDirectory: 'Bab',
    hasAnnualPack: true,
    isMasterData: false
  },
  
  // O系（オッズデータ）- 日付単位で更新、年度パックなし
  [JRDBDataType.OZ]: {
    dataType: JRDBDataType.OZ,
    description: '基準オッズデータ（単複・馬連）',
    specificationUrl: 'https://jrdb.com/program/Oz/Ozdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Oz',
    dataFileDirectory: 'Oz',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.OW]: {
    dataType: JRDBDataType.OW,
    description: '基準オッズデータ（ワイド）',
    specificationUrl: 'https://jrdb.com/program/Oz/Owdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Oz',
    dataFileDirectory: 'Oz',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.OU]: {
    dataType: JRDBDataType.OU,
    description: '基準馬単データ',
    specificationUrl: 'https://jrdb.com/program/Ou/Oudata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ou',
    dataFileDirectory: 'Ou',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.OT]: {
    dataType: JRDBDataType.OT,
    description: '基準３連複データ',
    specificationUrl: 'https://jrdb.com/program/Ot/Otdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ot',
    dataFileDirectory: 'Ot',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.OV]: {
    dataType: JRDBDataType.OV,
    description: '基準３連単データ',
    specificationUrl: 'https://jrdb.com/program/Ov/ovdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ov',
    dataFileDirectory: 'Ov',
    hasAnnualPack: false,
    isMasterData: false
  },
  
  // HJ系（払戻情報データ）- 日付単位で更新
  [JRDBDataType.HJC]: {
    dataType: JRDBDataType.HJC,
    description: '払戻情報データ（レース結果・払戻金）',
    specificationUrl: 'https://jrdb.com/program/Hjc/hjcdata_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Hjc',
    dataFileDirectory: 'Hjc',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.HJB]: {
    dataType: JRDBDataType.HJB,
    description: '払戻情報データ（レース結果・払戻金）',
    specificationUrl: 'https://jrdb.com/program/Hjb/hjb_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Hjb',
    dataFileDirectory: 'Hjb',
    hasAnnualPack: false,
    isMasterData: false
  },
  
  // SE系（成績データ）- 日付単位で更新、年度パックあり
  // 注意: SRBとSRAはSED/SECに同梱されているため、個別のデータタイプとして定義しない
  [JRDBDataType.SED]: {
    dataType: JRDBDataType.SED,
    description: '成績速報データ（レース結果詳細）',
    specificationUrl: 'https://jrdb.com/program/Sed/sed_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Sed',
    dataFileDirectory: 'Sed',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.SEC]: {
    dataType: JRDBDataType.SEC,
    description: '成績速報データ（レース結果詳細）',
    specificationUrl: 'https://jrdb.com/program/Sec/sec_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Sec',
    dataFileDirectory: 'Sec',
    hasAnnualPack: true,
    isMasterData: false
  },
  
  // ZE系（前走データ）- 成績データと同じフォーマット、年度パックなし
  [JRDBDataType.ZED]: {
    dataType: JRDBDataType.ZED,
    description: '前走データ（過去5走の成績・予測に必須）',
    specificationUrl: 'https://jrdb.com/program/Sed/sed_doc.txt', // ZEDはSEDと同じフォーマット
    dataFileBaseUrl: 'https://jrdb.com/member/data/Zed',
    dataFileDirectory: 'Zed',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.ZEC]: {
    dataType: JRDBDataType.ZEC,
    description: '前走データ（過去5走の成績・予測に必須）',
    specificationUrl: 'https://jrdb.com/program/Sec/sec_doc.txt', // ZECはSECと同じフォーマット
    dataFileBaseUrl: 'https://jrdb.com/member/data/Zec',
    dataFileDirectory: 'Zec',
    hasAnnualPack: false,
    isMasterData: false
  },
  
  // その他 - 日付単位で更新
  [JRDBDataType.UKC]: {
    dataType: JRDBDataType.UKC,
    description: '馬基本データ（血統登録番号・性別・生年月日・血統情報）',
    specificationUrl: 'https://jrdb.com/program/Ukc/ukc_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ukc',
    dataFileDirectory: 'Ukc',
    hasAnnualPack: true,
    isMasterData: false
  },
  [JRDBDataType.JOA]: {
    dataType: JRDBDataType.JOA,
    description: '情報データ（詳細情報による予想精度向上）',
    specificationUrl: 'https://jrdb.com/program/Jo/Jodata_doc2.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Jo',
    dataFileDirectory: 'Jo',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.TYB]: {
    dataType: JRDBDataType.TYB,
    description: '直前情報データ（出走直前の馬の状態・当日予想に最重要）',
    specificationUrl: 'https://jrdb.com/program/Tyb/tyb_doc.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Tyb',
    dataFileDirectory: 'Tyb',
    hasAnnualPack: true,
    isMasterData: false
  },
  
  // 騎手・調教師データ（週単位で更新）- 年度パックなし、マスターデータ
  [JRDBDataType.KZA]: {
    dataType: JRDBDataType.KZA,
    description: '騎手データ（全騎手分・勝率・連対率・予測に必須）',
    specificationUrl: 'https://jrdb.com/program/Ks/Ks_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ks',
    dataFileDirectory: 'Ks',
    hasAnnualPack: false,
    isMasterData: true
  },
  [JRDBDataType.KSA]: {
    dataType: JRDBDataType.KSA,
    description: '騎手データ（今週出走分・勝率・連対率・予測に必須）',
    specificationUrl: 'https://jrdb.com/program/Ks/Ks_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Ks',
    dataFileDirectory: 'Ks',
    hasAnnualPack: false,
    isMasterData: false
  },
  [JRDBDataType.CZA]: {
    dataType: JRDBDataType.CZA,
    description: '調教師データ（全調教師分・勝率・連対率・予測に必須）',
    specificationUrl: 'https://jrdb.com/program/Cs/Cs_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Cs',
    dataFileDirectory: 'Cs',
    hasAnnualPack: false,
    isMasterData: true
  },
  [JRDBDataType.CSA]: {
    dataType: JRDBDataType.CSA,
    description: '調教師データ（今週出走分・勝率・連対率・予測に必須）',
    specificationUrl: 'https://jrdb.com/program/Cs/Cs_doc1.txt',
    dataFileBaseUrl: 'https://jrdb.com/member/data/Cs',
    dataFileDirectory: 'Cs',
    hasAnnualPack: false,
    isMasterData: false
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

/**
 * 年度パックのURLを生成
 * @param dataType - データタイプ
 * @param year - 年度（例: 2024）
 * @returns 年度パックのURL（例: `https://jrdb.com/member/data/Tyb/TYB_2024.lzh`）
 * @throws {Error} 年度パックが提供されていないデータタイプの場合
 */
export function generateAnnualPackUrl(dataType: JRDBDataType, year: number): string {
  const info = JRDB_DATA_TYPE_INFO[dataType]
  if (!info.hasAnnualPack) throw new Error(`データタイプ ${dataType} には年度パックが提供されていません`)
  const fileName = `${dataType}_${year}.lzh`
  return `${info.dataFileBaseUrl}/${fileName}`
}

/**
 * データタイプに年度パックが提供されているか判定（動的チェック）
 * メンバーページのindex.htmlにアクセスして確認
 * 
 * 注意: この関数は実際にHTTPリクエストを送信するため、頻繁に呼び出すと負荷がかかります。
 * 結果をキャッシュすることを推奨します。
 */
export async function checkAnnualPackAvailability(dataType: JRDBDataType): Promise<boolean> {
  const { checkAnnualPackAvailability: checkAvailability } = await import('../formats/converter/memberPageChecker')
  return checkAvailability(dataType)
}

export function getAllDataTypes(): JRDBDataType[] {
  return Object.values(JRDBDataType)
}