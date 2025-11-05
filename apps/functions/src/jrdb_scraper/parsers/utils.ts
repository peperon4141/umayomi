import { logger } from 'firebase-functions'
import * as iconv from 'iconv-lite'

/**
 * JRDBフィールドの型種別
 */
export enum JRDBFieldType {
  STRING = 'string',
  INTEGER = 'integer',
  FLOAT = 'float'
}

/**
 * JRDBフィールド定義の型
 */
export interface JRDBFieldDefinition {
  name: string
  start: number
  length: number
  type: JRDBFieldType
  description: string
}

/**
 * JRDBフォーマット定義の型
 */
export interface JRDBFormatDefinition {
  dataType: string
  description: string
  recordLength: number
  encoding: string
  lineEnding: string
  specificationUrl?: string
  usageGuideUrl?: string
  sampleUrl?: string
  fields: JRDBFieldDefinition[]
  note?: string
}

/**
 * ShiftJISバッファから指定位置・長さで値を抽出（バイト位置ベース）
 */
export function extractFieldValueFromBuffer(buffer: Buffer, field: JRDBFieldDefinition): unknown {
  const startIndex = field.start - 1 // 1ベースから0ベースに変換
  const endIndex = startIndex + field.length
  const fieldBuffer = buffer.slice(startIndex, endIndex)
  const rawValue = iconv.decode(fieldBuffer, 'shift_jis').trim()

  if (rawValue === '' || rawValue === '0' || rawValue === '0.0') {
    return null
  }

  switch (field.type) {
    case JRDBFieldType.INTEGER: {
      const intValue = parseInt(rawValue, 10)
      return isNaN(intValue) ? null : intValue
    }
    case JRDBFieldType.FLOAT: {
      const floatValue = parseFloat(rawValue)
      return isNaN(floatValue) ? null : floatValue
    }
    case JRDBFieldType.STRING:
    default:
      return rawValue
  }
}

/**
 * 固定長テキストから指定位置・長さで値を抽出（UTF-8文字列用、後方互換性のため保持）
 */
export function extractFieldValue(line: string, field: JRDBFieldDefinition): unknown {
  const startIndex = field.start - 1 // 1ベースから0ベースに変換
  const endIndex = startIndex + field.length
  const rawValue = line.substring(startIndex, endIndex).trim()

  if (rawValue === '' || rawValue === '0' || rawValue === '0.0') {
    return null
  }

  switch (field.type) {
    case JRDBFieldType.INTEGER: {
      const intValue = parseInt(rawValue, 10)
      return isNaN(intValue) ? null : intValue
    }
    case JRDBFieldType.FLOAT: {
      const floatValue = parseFloat(rawValue)
      return isNaN(floatValue) ? null : floatValue
    }
    case JRDBFieldType.STRING:
    default:
      return rawValue
  }
}

/**
 * 固定長テキストの1行を解析（汎用関数）
 */
export function parseRecord(line: string, format: JRDBFormatDefinition): Record<string, unknown> {
  const record: Record<string, unknown> = {}

  for (const field of format.fields) {
    const value = extractFieldValue(line, field)
    record[field.name] = value
  }

  return record
}

/**
 * JRDBデータをパース（汎用関数）
 * @param text - ShiftJISでエンコードされたテキスト（UTF-8に変換済み）
 * @param format - フォーマット定義
 * @returns パースされたレコードの配列
 */
export function parseData(text: string, format: JRDBFormatDefinition): Record<string, unknown>[] {
  logger.info('JRDBデータのパース開始', { dataType: format.dataType, textLength: text.length })

  const records: Record<string, unknown>[] = []
  const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0)

  logger.info('JRDBデータを行に分割', { dataType: format.dataType, totalLines: lines.length })

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // ShiftJIS→UTF-8変換により文字数が変わるため、レコード長チェックを緩和
    // 期待値の85%以上であれば処理を続行（ShiftJISの2バイト文字がUTF-8の3バイトに変換されるため）
    const minLength = Math.floor(format.recordLength * 0.85)
    if (line.length < minLength) {
      logger.warn('レコード長が不足しています', {
        dataType: format.dataType,
        lineNumber: i + 1,
        expectedLength: format.recordLength,
        actualLength: line.length,
        minLength
      })
      continue
    }

    try {
      const record = parseRecord(line, format)
      records.push(record)
    } catch (error) {
      logger.error('JRDBレコードのパースに失敗', {
        dataType: format.dataType,
        lineNumber: i + 1,
        error: error instanceof Error ? error.message : String(error),
        linePreview: line.substring(0, 100)
      })
    }
  }

  logger.info('JRDBデータのパース完了', { dataType: format.dataType, totalRecords: records.length })

  return records
}

/**
 * ShiftJISバッファからJRDBデータをパース（汎用関数）
 * ShiftJISのバイト位置で正確にパースする
 * @param buffer - ShiftJISでエンコードされたバッファ
 * @param format - フォーマット定義
 * @returns パースされたレコードの配列
 */
export function parseDataFromBuffer(buffer: Buffer, format: JRDBFormatDefinition): Record<string, unknown>[] {
  logger.info('JRDBデータのパース開始（ShiftJISバッファ）', { dataType: format.dataType, bufferLength: buffer.length })

  const records: Record<string, unknown>[] = []
  const recordLength = format.recordLength
  const lineEnding = format.lineEnding === 'CRLF' ? Buffer.from([0x0D, 0x0A]) : Buffer.from([0x0A])
  const lineEndingLength = lineEnding.length

  let offset = 0
  let lineNumber = 0

  while (offset < buffer.length) {
    // 改行コードを探す
    const lineEndIndex = buffer.indexOf(lineEnding, offset)
    if (lineEndIndex === -1) {
      // 最後のレコード（改行コードなし）
      if (buffer.length - offset >= recordLength * 0.9) {
        const recordBuffer = buffer.slice(offset, offset + recordLength)
        try {
          const record = parseRecordFromBuffer(recordBuffer, format)
          records.push(record)
        } catch (error) {
          logger.error('JRDBレコードのパースに失敗', {
            dataType: format.dataType,
            lineNumber: lineNumber + 1,
            error: error instanceof Error ? error.message : String(error)
          })
        }
      }
      break
    }

    const lineBuffer = buffer.slice(offset, lineEndIndex)
    offset = lineEndIndex + lineEndingLength

    // 空行をスキップ
    if (lineBuffer.length === 0) continue

    // レコード長チェック（バイト単位）
    if (lineBuffer.length < recordLength * 0.9) {
      logger.warn('レコード長が不足しています', {
        dataType: format.dataType,
        lineNumber: lineNumber + 1,
        expectedLength: recordLength,
        actualLength: lineBuffer.length
      })
      continue
    }

    // レコード長分だけ切り出す
    const recordBuffer = lineBuffer.slice(0, recordLength)

    try {
      const record = parseRecordFromBuffer(recordBuffer, format)
      records.push(record)
    } catch (error) {
      logger.error('JRDBレコードのパースに失敗', {
        dataType: format.dataType,
        lineNumber: lineNumber + 1,
        error: error instanceof Error ? error.message : String(error)
      })
    }

    lineNumber++
  }

  logger.info('JRDBデータのパース完了（ShiftJISバッファ）', { dataType: format.dataType, totalRecords: records.length })

  return records
}

/**
 * ShiftJISバッファの1レコードを解析（バイト位置ベース）
 */
function parseRecordFromBuffer(recordBuffer: Buffer, format: JRDBFormatDefinition): Record<string, unknown> {
  const record: Record<string, unknown> = {}

  for (const field of format.fields) {
    const value = extractFieldValueFromBuffer(recordBuffer, field)
    record[field.name] = value
  }

  return record
}

