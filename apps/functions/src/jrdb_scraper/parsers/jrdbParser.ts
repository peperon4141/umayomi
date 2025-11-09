import { logger } from 'firebase-functions'
import { JRDBDataType } from '../entities/jrdb'
import { kyiFormat } from '../formats/kyi'
import { kyhFormat } from '../formats/kyh'
import { kygFormat } from '../formats/kyg'
import { kkaFormat } from '../formats/kka'
import { bacFormat } from '../formats/bac'
import { babFormat } from '../formats/bab'
import { ozFormat } from '../formats/oz'
import { owFormat } from '../formats/ow'
import { ouFormat } from '../formats/ou'
import { otFormat } from '../formats/ot'
import { ovFormat } from '../formats/ov'
import { hjcFormat } from '../formats/hjc'
import { hjbFormat } from '../formats/hjb'
import { sedFormat } from '../formats/sed'
import { secFormat } from '../formats/sec'
import { zedFormat } from '../formats/zed'
import { zecFormat } from '../formats/zec'
import { joaFormat } from '../formats/joa'
import { tybFormat } from '../formats/tyb'
import { ukcFormat } from '../formats/ukc'
import { kzaFormat } from '../formats/kza'
import { ksaFormat } from '../formats/ksa'
import { czaFormat } from '../formats/cza'
import { csaFormat } from '../formats/csa'
import type { JRDBFormatDefinition } from './formatParser'
import { parseDataFromBuffer } from './formatParser'

/**
 * データ種別からフォーマット定義を取得
 */
export function getFormatDefinition(dataType: JRDBDataType): JRDBFormatDefinition | null {
  switch (dataType) {
    case JRDBDataType.KYI: return kyiFormat
    case JRDBDataType.KYH: return kyhFormat
    case JRDBDataType.KYG: return kygFormat
    case JRDBDataType.KKA: return kkaFormat
    case JRDBDataType.BAC: return bacFormat
    case JRDBDataType.BAB: return babFormat
    case JRDBDataType.OZ: return ozFormat
    case JRDBDataType.OW: return owFormat
    case JRDBDataType.OU: return ouFormat
    case JRDBDataType.OT: return otFormat
    case JRDBDataType.OV: return ovFormat
    case JRDBDataType.HJC: return hjcFormat
    case JRDBDataType.HJB: return hjbFormat
    // SRBとSRAはSED/SECに同梱されているため、個別のパーサーは不要
    case JRDBDataType.SED: return sedFormat
    case JRDBDataType.SEC: return secFormat
    case JRDBDataType.ZED: return zedFormat
    case JRDBDataType.ZEC: return zecFormat
    case JRDBDataType.JOA: return joaFormat
    case JRDBDataType.TYB: return tybFormat
    case JRDBDataType.UKC: return ukcFormat
    case JRDBDataType.KZA: return kzaFormat
    case JRDBDataType.KSA: return ksaFormat
    case JRDBDataType.CZA: return czaFormat
    case JRDBDataType.CSA: return csaFormat
    default: return null
  }
}

/**
 * データタイプ文字列からフォーマット定義を取得
 */
export function getFormatDefinitionFromString(dataType: string): JRDBFormatDefinition | null {
  const enumValue = Object.values(JRDBDataType).find(v => v === dataType)
  if (!enumValue) throw new Error(`未定義のデータタイプです: ${dataType}`)
  return getFormatDefinition(enumValue)
}

/**
 * ファイル名からコードと日付を解析
 * @param fileName - ファイル名（例: "KYG251102.lzh", "KYI251102.lzh", "BAB_2024.lzh"）
 * @returns コードと日付情報、解析に失敗した場合はnull
 */
export function parseJRDBFileName(fileName: string): { dataType: JRDBDataType, year: number, month?: number, day?: number } | null {
  // 汎用的なパターン: アルファベット + (オプションの区切り文字) + 数字(4-6桁) + 拡張子
  // 例: KYI251102.lzh, BAB_2024.lzh, KYG251102.txt
  const match = fileName.match(/^([A-Z]+)_?(\d{4,6})\.(lzh|txt)$/i)
  if (!match || !match[1] || !match[2]) return null
  
  const dataType = findJrdbDateType(match[1].toUpperCase())
  if (!dataType) return null

  const dateStr = match[2]
  // 6桁の場合はYYMMDD形式として解析
  if (dateStr.length === 6) {
    const year = parseInt('20' + dateStr.substring(0, 2))
    const month = parseInt(dateStr.substring(2, 4))
    const day = parseInt(dateStr.substring(4, 6))
    if (!isNaN(year) && !isNaN(month) && !isNaN(day)) return { dataType, year, month, day }
  }
  
  // 4桁の場合は年のみとして解析
  if (dateStr.length === 4) {
    const year = parseInt(dateStr)
    if (!isNaN(year)) return { dataType, year: parseInt(dateStr) }
  }
  
  return null
}

/**
 * 文字列からJRDBDataTypeに変換
 * @param dataType - データ型コード文字列
 * @returns マッチするJRDBDataType、見つからない場合はnull
 */
export function findJrdbDateType(dataType: string): JRDBDataType | null {
  const upperDataType = dataType.toUpperCase()
  const codeEnum = Object.values(JRDBDataType).find(v => v.toUpperCase() === upperDataType)
  return codeEnum || null
}

/**
 * JRDBデータをパース（汎用関数）
 * @param buffer - ShiftJISでエンコードされたバッファ
 * @param dataType - データ種別（enumまたは文字列）
 * @returns パースされたレコードの配列
 */
export function parseJRDBDataFromBuffer(
  buffer: Buffer,
  dataType: JRDBDataType | string
): Record<string, unknown>[] {
  let format: JRDBFormatDefinition | null = null
  
  if (typeof dataType === 'string') format = getFormatDefinitionFromString(dataType)
  else format = getFormatDefinition(dataType)

  if (!format) {
    logger.warn('対応していないデータ種別です', { dataType })
    return []
  }
  
  return parseDataFromBuffer(buffer, format)
}

