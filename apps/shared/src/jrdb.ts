/**
 * JRDBデータの型定義
 * JRDBデータは固定長テキスト形式で提供される
 */

/**
 * JRDBデータ種別
 */
export enum JRDBDataType {
  KY = 'KY', // 競走馬データ（汎用）
  KYI = 'KYI', // 競走馬データ（牧場先情報付き）
  KYH = 'KYH', // 競走馬データ（標準版）
  KYG = 'KYG', // 競走馬データ（標準版）
  KKA = 'KKA', // 競走馬拡張データ（KY系）
  UK = 'UK', // 馬基本データ
  ZE = 'ZE', // 前走データ
  ZK = 'ZK', // 前走拡張データ
  BA = 'BA', // 番組データ
  OZ = 'OZ', // 基準オッズデータ（単複、馬連）
  OW = 'OW', // 基準オッズデータ（ワイド）
  OU = 'OU', // 基準馬単データ
  OT = 'OT', // 基準３連複データ
  OV = 'OV', // 基準３連単データ
  JO = 'JO', // 情報データ
  KK = 'KK', // 競走馬拡張データ
  TY = 'TY', // 直前情報データ
  HJ = 'HJ', // 払戻情報データ
  SE = 'SE', // 成績データ
  SR = 'SR', // 成績レースデータ
  SK = 'SK', // 成績拡張データ
  KZ = 'KZ', // 騎手データ（全騎手分）
  KS = 'KS', // 騎手データ（今週出走分）
  CZ = 'CZ', // 調教師データ（全調教師分）
  CS = 'CS', // 調教師データ（今週出走分）
  MZ = 'MZ', // 抹消馬データ（1999年以降）
  MS = 'MS' // 抹消馬データ（先週～今週）
}

/**
 * JRDBデータの基本情報
 */
export interface JRDBDataInfo {
  dataType: JRDBDataType
  year: number
  encoding?: 'ShiftJIS' | 'UTF-8'
}

/**
 * Parquet変換時のスキーマ定義（基本型）
 * 実際のスキーマはデータ種別ごとに定義する必要がある
 */
export interface ParquetSchemaField {
  name: string
  type: 'UTF8' | 'INT32' | 'INT64' | 'DOUBLE' | 'BOOLEAN' | 'TIMESTAMP_MILLIS'
  optional?: boolean
}

