import { logger } from 'firebase-functions'
import * as iconv from 'iconv-lite'

/**
 * JRDBフィールドの型種別
 */
/* eslint-disable no-unused-vars */
export enum JRDBFieldType {
  STRING = 'string',
  INTEGER = 'integer',
  FLOAT = 'float'
}
/* eslint-enable no-unused-vars */

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
 * 仕様書に基づいて、ShiftJISバッファからバイト位置で分割してからUTF-8に変換する
 */
export function extractFieldValueFromBuffer(buffer: Buffer, field: JRDBFieldDefinition): unknown {
  const startIndex = field.start - 1 // 1ベースから0ベースに変換（仕様書は1ベース）
  const endIndex = startIndex + field.length
  
  // バッファの範囲チェック
  if (startIndex < 0 || endIndex > buffer.length) {
    logger.warn('Field buffer range out of bounds', {
      fieldName: field.name,
      startIndex,
      endIndex,
      bufferLength: buffer.length,
      fieldStart: field.start,
      fieldLength: field.length
    })
    return null
  }
  
  // ShiftJISバッファからバイト位置でフィールドを抽出（仕様書に基づく分割）
  const fieldBuffer = buffer.slice(startIndex, endIndex)
  
  // バッファが空の場合はnullを返す
  if (fieldBuffer.length === 0) {
    return null
  }
  
  // 抽出したバイト列をShiftJISからUTF-8に変換
  // 仕様書に基づいて、ShiftJISバッファからバイト位置で分割してからUTF-8に変換
  // 注意: ShiftJISの2バイト文字がフィールド境界で切れている可能性があるため、
  // フィールドの開始位置と終了位置を調整して変換を試みる
  let rawValue: string
  
  // ShiftJISの2バイト文字の開始バイトを検出
  const isShiftJISFirstByte = (byte: number): boolean => {
    return (byte >= 0x81 && byte <= 0x9F) || (byte >= 0xE0 && byte <= 0xFC)
  }
  
  // ShiftJISの2バイト文字の2バイト目を検出
  const isShiftJISSecondByte = (byte: number): boolean => {
    return (byte >= 0x40 && byte <= 0x7E) || (byte >= 0x80 && byte <= 0xFC)
  }
  
  // フィールドの開始位置を調整（前のフィールドの2バイト文字の途中で終わっている場合）
  let adjustedStart = startIndex
  if (startIndex > 0) {
    const prevByte = buffer[startIndex - 1]
    // 前のバイトが2バイト文字の最初のバイトの場合、前のフィールドが2バイト文字の途中で終わっている
    // この場合、フィールドの開始位置を1バイト前に調整
    if (isShiftJISFirstByte(prevByte)) {
      adjustedStart = Math.max(0, startIndex - 1)
    }
    // 開始位置のバイトが2バイト文字の2バイト目の場合、前のフィールドが2バイト文字の途中で終わっている
    else if (isShiftJISSecondByte(buffer[startIndex]) && startIndex > 1) {
      const prevPrevByte = buffer[startIndex - 2]
      if (isShiftJISFirstByte(prevPrevByte)) {
        adjustedStart = Math.max(0, startIndex - 2)
      }
    }
  }
  
  // フィールドの終了位置を調整（次のフィールドの2バイト文字の途中で始まっている場合）
  let adjustedEnd = endIndex
  if (endIndex < buffer.length) {
    // 終了位置の次のバイトが2バイト文字の最初のバイトの場合、そのバイトも含める
    if (isShiftJISFirstByte(buffer[endIndex])) {
      adjustedEnd = Math.min(buffer.length, endIndex + 2) // 2バイト文字全体を含める
    }
    // 終了位置のバイトが2バイト文字の最初のバイトの場合、そのバイトも含める
    else if (isShiftJISFirstByte(buffer[endIndex - 1]) && endIndex < buffer.length) {
      adjustedEnd = Math.min(buffer.length, endIndex + 1)
    }
  }
  
  // 調整された範囲で変換を試みる
  try {
    // まず、元のフィールド範囲だけで変換を試みる
    rawValue = iconv.decode(fieldBuffer, 'shift_jis').trim()
    
    // 文字化けを検出（U+FFFDまたは制御文字が含まれている場合）
    // eslint-disable-next-line no-control-regex
    const hasInvalidChars = rawValue.includes('\uFFFD') || /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/.test(rawValue)
    
    if (hasInvalidChars && (adjustedStart < startIndex || adjustedEnd > endIndex)) {
      // 調整された範囲で変換を試みる
      const adjustedBuffer = buffer.slice(adjustedStart, adjustedEnd)
      const decodedValue = iconv.decode(adjustedBuffer, 'shift_jis')
      
      // 元のフィールド範囲を文字列から抽出
      // 調整範囲の先頭から、元のフィールド開始位置までのバイト数を文字数に変換
      const prefixBytes = startIndex - adjustedStart
      const fieldBytes = endIndex - startIndex
      
      // バイト位置から文字位置への変換（簡易版: 先頭と末尾を適切にトリム）
      // 調整範囲全体を変換した後、先頭の調整分を削除
      let prefixCharCount = 0
      let byteCount = 0
      for (let i = 0; i < decodedValue.length && byteCount < prefixBytes; i++) {
        const charCode = decodedValue.charCodeAt(i)
        // ShiftJISの2バイト文字はUTF-8で3バイトになることが多い
        byteCount += charCode > 0x7F ? 2 : 1
        if (byteCount <= prefixBytes) {
          prefixCharCount = i + 1
        }
      }
      
      // フィールド範囲の文字数を概算
      let fieldCharCount = 0
      byteCount = 0
      for (let i = prefixCharCount; i < decodedValue.length && byteCount < fieldBytes; i++) {
        const charCode = decodedValue.charCodeAt(i)
        byteCount += charCode > 0x7F ? 2 : 1
        if (byteCount <= fieldBytes) {
          fieldCharCount = i - prefixCharCount + 1
        }
      }
      
      rawValue = decodedValue.substring(prefixCharCount, prefixCharCount + fieldCharCount).trim()
      
      // それでも文字化けが残る場合、ASCIIフォールバックを使用
      // eslint-disable-next-line no-control-regex
      if (rawValue.includes('\uFFFD') || /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/.test(rawValue)) {
        rawValue = Array.from(fieldBuffer)
          .map(b => {
            if (b >= 0x20 && b <= 0x7E) {
              return String.fromCharCode(b)
            } else if (b >= 0xA1 && b <= 0xDF) {
              return String.fromCharCode(b)
            }
            return ''
          })
          .join('')
          .trim()
      }
    } else if (hasInvalidChars) {
      // ASCIIフォールバックを使用
      rawValue = Array.from(fieldBuffer)
        .map(b => {
          if (b >= 0x20 && b <= 0x7E) {
            return String.fromCharCode(b)
          } else if (b >= 0xA1 && b <= 0xDF) {
            return String.fromCharCode(b)
          }
          return ''
        })
        .join('')
        .trim()
    }
    
    // KKAのレースキーの「日」フィールド（6バイト目、1バイト）は16進数形式
    // 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
    // 「日 1 F 6 16進数(日付 or 開催回数、日目)」
    // 16進数文字列を10進数に変換する必要がある
    if (field.name === 'レースキー' && field.start === 6 && field.length === 1) {
      // 16進数として解釈して10進数に変換
      try {
        const hexValue = parseInt(rawValue, 16)
        if (!isNaN(hexValue)) {
          rawValue = hexValue.toString()
        }
      } catch {
        // 変換失敗時は元の値を保持
      }
    }
  } catch {
    // ShiftJIS変換に失敗した場合、ASCIIとして解釈を試みる
    rawValue = Array.from(fieldBuffer)
      .map(b => (b >= 0x20 && b <= 0x7E) ? String.fromCharCode(b) : '')
      .join('')
      .trim()
  }

  // 空文字列や0の場合はnullを返す（数値フィールドの場合）
  if (rawValue === '' || rawValue === '0' || rawValue === '0.0') {
    return null
  }

  // フィールドタイプに応じて変換
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
      // 文字列フィールドはそのまま返す（レースキーなど）
      // ただし、KKAのレースキーの「日」フィールド（6バイト目）は16進数形式のため、
      // レースキー全体をパースした後、6バイト目の文字を16進数→10進数に変換する必要がある
      // この処理は、レースキーフィールド全体をパースする際に行う
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
    if (offset < buffer.length) {
      if (buffer[offset] === 0x0D && buffer[offset + 1] === 0x0A) {
        offset += 2
      } else if (buffer[offset] === 0x0A) {
        offset += 1
      }
    }

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
    if (raceKey && raceKey.length >= 6) {
      try {
        // 6バイト目（0ベースで5番目）の文字を16進数から10進数に変換
        const hexChar = raceKey[5]
        const decimalValue = parseInt(hexChar, 16)
        if (!isNaN(decimalValue) && decimalValue >= 0 && decimalValue <= 15) {
          // 6バイト目の文字を10進数に置き換え
          record['レースキー'] = raceKey.substring(0, 5) + decimalValue.toString() + raceKey.substring(6)
        }
      } catch {
        // 変換失敗時は元の値を保持
      }
    }
  }

  return record
}

