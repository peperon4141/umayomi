import * as iconv from 'iconv-lite'
import type { JRDBFieldDefinition } from './formatParser'

/**
 * JRDBフィールドの型種別
 * JRDB仕様書のTYPE（9/Z/X/F）に基づく
 * - 9: 数字 (0のとき0)
 * - Z: 数字（0のとき空白）
 * - X: 文字
 * - F: 16進数(数字 or 小文字アルファベット)
 */
/* eslint-disable no-unused-vars */
export enum JRDBFieldType {
  // 9型: 数字 (0のとき0)
  INTEGER_NINE = 'integer_nine',
  // Z型: 数字（0のとき空白）
  INTEGER_ZERO_BLANK = 'integer_zero_blank',
  // X型: 文字
  STRING = 'string',
  // F型: 16進数(数字 or 小文字アルファベット)
  STRING_HEX = 'string_hex'
}
/* eslint-enable no-unused-vars */

/**
 * ShiftJISバッファから指定位置・長さで値を抽出（バイト位置ベース）
 * 仕様書に基づいて、ShiftJISバッファからバイト位置で分割してからUTF-8に変換する
 */
export function extractFieldValueFromBuffer(buffer: Buffer, field: JRDBFieldDefinition): unknown {
  const startIndex = field.start - 1 // 1ベースから0ベースに変換（仕様書は1ベース）
  const endIndex = startIndex + field.length
  
  if (startIndex < 0 || endIndex > buffer.length) return null
  
  // ShiftJISバッファからバイト位置でフィールドを抽出（仕様書に基づく分割）
  const fieldBuffer = buffer.slice(startIndex, endIndex)
  
  // バッファが空の場合はnullを返す
  if (fieldBuffer.length === 0) return null
  
  // 抽出したバイト列をShiftJISからUTF-8に変換
  let rawValue: string
  try {
    rawValue = iconv.decode(fieldBuffer, 'shift_jis').trim()
  } catch {
    // ShiftJIS変換に失敗した場合、ASCIIとして解釈を試みる
    rawValue = Array.from(fieldBuffer)
      .map(b => (b >= 0x20 && b <= 0x7E) ? String.fromCharCode(b) : '')
      .join('')
      .trim()
  }
  
  // KKAのレースキーの「日」フィールド（6バイト目、1バイト）は16進数形式
  // 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
  // 「日 1 F 6 16進数(日付 or 開催回数、日目)」
  // 16進数文字列を10進数に変換する必要がある
  if (field.name === 'レースキー' && field.start === 6 && field.length === 1) 
    // 16進数として解釈して10進数に変換
    try {
      const hexValue = parseInt(rawValue, 16)
      if (!isNaN(hexValue)) rawValue = hexValue.toString()
    } catch {
      // 変換失敗時は元の値を保持
    }
  

  // JRDB TYPEに応じた処理
  return convertFieldValue(rawValue, field.type)
}

/**
 * 固定長テキストから指定位置・長さで値を抽出（UTF-8文字列用、後方互換性のため保持）
 */
export function extractFieldValue(line: string, field: JRDBFieldDefinition): unknown {
  const startIndex = field.start - 1 // 1ベースから0ベースに変換
  const endIndex = startIndex + field.length
  const rawValue = line.substring(startIndex, endIndex).trim()

  // JRDB TYPEに応じた処理
  return convertFieldValue(rawValue, field.type)
}

/**
 * フィールドの生値を型に応じて変換
 */
function convertFieldValue(rawValue: string, fieldType: JRDBFieldType): unknown {
  // INTEGER_ZERO_BLANK (Z型)の場合、空文字列はnull（0のとき空白）
  if (fieldType === JRDBFieldType.INTEGER_ZERO_BLANK && rawValue === '') return null
  
  // INTEGER_NINE (9型)以外の数値型の場合、空文字列や0の場合はnullを返す
  // INTEGER_NINE (9型)の場合は0も有効な値なので、nullにしない
  if (fieldType !== JRDBFieldType.INTEGER_NINE && (rawValue === '' || rawValue === '0' || rawValue === '0.0')) 
    // INTEGER_ZERO_BLANK (Z型)の場合は既に処理済み
    if (fieldType === JRDBFieldType.INTEGER_ZERO_BLANK) return null
  
  
  // フィールドタイプに応じて変換
  switch (fieldType) {
    case JRDBFieldType.INTEGER_NINE: {
      const intValue = parseInt(rawValue, 10)
      // 0も有効な値
      if (intValue === 0) return 0
      return isNaN(intValue) ? null : intValue
    }
    case JRDBFieldType.INTEGER_ZERO_BLANK: {
      const intValue = parseInt(rawValue, 10)
      return isNaN(intValue) ? null : intValue
    }
    case JRDBFieldType.STRING:
    case JRDBFieldType.STRING_HEX:
    default: return rawValue
  }
}
