import { logger } from 'firebase-functions'
import { extractFieldValue, extractFieldValueFromBuffer } from './fieldParser'
import type { JRDBFieldType } from './fieldParser'

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

// extractFieldValueFromBuffer と extractFieldValue は fieldParser.ts に移動

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

  // 固定長レコードとして処理（改行コードに関係なく、recordLengthごとに切り出す）
  let offset = 0
  let lineNumber = 0

  while (offset + recordLength <= buffer.length) {
    // レコードを切り出す（recordLengthバイト）
    const recordBuffer = buffer.slice(offset, offset + recordLength)
    
    // レコード長が正確でない場合はスキップ
    if (recordBuffer.length !== recordLength) {
      logger.warn('Record buffer length mismatch', {
        dataType: format.dataType,
        expectedLength: recordLength,
        actualLength: recordBuffer.length,
        lineNumber: lineNumber + 1
      })
      break
    }
    
    offset += recordLength

    // 改行コードをスキップ（CRLFまたはLF）- レコードの後に改行がある場合
    if (offset < buffer.length) 
      if (buffer[offset] === 0x0D && buffer[offset + 1] === 0x0A) offset += 2
      else if (buffer[offset] === 0x0A) offset += 1
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

  // KKAのレースキーの「日」フィールド（6バイト目）は16進数形式（TYPE F）
  // 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
  // 「日 1 F 6 16進数(日付 or 開催回数、日目)」
  // レースキー全体をパースした後、6バイト目（0ベースで5番目）の文字を16進数→10進数に変換
  if (format.dataType === 'KKA' && record['レースキー']) {
    const raceKey = record['レースキー'] as string
    if (raceKey && raceKey.length >= 6) 
      try {
        // 6バイト目（0ベースで5番目）の文字を16進数から10進数に変換
        const hexChar = raceKey[5]
        const decimalValue = parseInt(hexChar, 16)
        if (!isNaN(decimalValue) && decimalValue >= 0 && decimalValue <= 15) record['レースキー'] = raceKey.substring(0, 5) + decimalValue.toString() + raceKey.substring(6)
        
      } catch {
        // 変換失敗時は元の値を保持
      }
    
  }

  return record
}

