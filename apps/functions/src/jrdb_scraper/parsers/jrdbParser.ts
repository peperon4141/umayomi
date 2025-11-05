import { logger } from 'firebase-functions'
import { JRDBDataType } from '../../../../shared/src/jrdb'
import { kyiFormat } from '../formats/kyi'
import { kyhFormat } from '../formats/kyh'
import { kygFormat } from '../formats/kyg'
import { kkaFormat } from '../formats/kka'
import type { JRDBFormatDefinition } from './utils'
import { parseDataFromBuffer } from './utils'

/**
 * データ種別からフォーマット定義を取得
 */
function getFormatDefinition(dataType: JRDBDataType): JRDBFormatDefinition | null {
  switch (dataType) {
    case JRDBDataType.KYI:
      return kyiFormat
    case JRDBDataType.KYH:
      return kyhFormat
    case JRDBDataType.KYG:
      return kygFormat
    case JRDBDataType.KKA:
      return kkaFormat
    default:
      return null
  }
}

/**
 * JRDBデータをパース（汎用関数）
 * @param buffer - ShiftJISでエンコードされたバッファ
 * @param dataType - データ種別（enum）
 * @returns パースされたレコードの配列
 */
export function parseJRDBDataFromBuffer(
  buffer: Buffer,
  dataType: JRDBDataType
): Record<string, unknown>[] {
  const format = getFormatDefinition(dataType)
  
  if (!format) {
    logger.warn('対応していないデータ種別です', { dataType })
    return []
  }
  
  return parseDataFromBuffer(buffer, format)
}

