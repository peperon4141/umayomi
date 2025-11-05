/**
 * JRDBデータの型定義
 * JRDBデータは固定長テキスト形式で提供される
 */

/**
 * JRDBデータ種別
 */
export type JRDBDataType =
  | 'KY' // 競走馬データ
  | 'UK' // 馬基本データ
  | 'ZE' // 前走データ
  | 'ZK' // 前走拡張データ
  | 'BA' // 番組データ
  | 'OZ' // 基準オッズデータ（単複、馬連）
  | 'OW' // 基準オッズデータ（ワイド）
  | 'OU' // 基準馬単データ
  | 'OT' // 基準３連複データ
  | 'OV' // 基準３連単データ
  | 'JO' // 情報データ
  | 'KK' // 競走馬拡張データ
  | 'TY' // 直前情報データ
  | 'HJ' // 払戻情報データ
  | 'SE' // 成績データ
  | 'SR' // 成績レースデータ
  | 'SK' // 成績拡張データ
  | 'KZ' // 騎手データ（全騎手分）
  | 'KS' // 騎手データ（今週出走分）
  | 'CZ' // 調教師データ（全調教師分）
  | 'CS' // 調教師データ（今週出走分）
  | 'MZ' // 抹消馬データ（1999年以降）
  | 'MS' // 抹消馬データ（先週～今週）

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

