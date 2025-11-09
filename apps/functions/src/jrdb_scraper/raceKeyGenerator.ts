/**
 * JRDBデータファイルURL生成ユーティリティ
 */

import { JRDBDataType, getJRDBDataTypeInfo } from './entities/jrdb'

/**
 * JRDBデータファイルURLを生成
 * @param dataType - データ種別（例: 'KYI', 'KYH', 'KYG', 'KKA'）
 * @param date - 日付（Date型）
 * @returns JRDBメンバーページのURL
 * 
 * 注意: 
 * - すべてのデータタイプ: `{dataType}{YYMMDD}.lzh` 形式（例: `KYI251102.lzh`, `KZA251108.lzh`, `MZA251108.lzh`）
 */
export function generateJRDBDataFileUrl(dataType: string, date: Date): string {
  const info = getJRDBDataTypeInfo(dataType as JRDBDataType)
  
  if (!info) throw new Error(`未定義のデータタイプ: ${dataType}. jrdbDataTypeInfo.tsに定義を追加してください。`)
  
  // すべてのデータタイプは日付を含める
  const year2Digit = String(date.getFullYear()).slice(-2)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const dateStr = `${year2Digit}${month}${day}`
  const fileName = `${dataType}${dateStr}.lzh`
  
  return `${info.dataFileBaseUrl}/${fileName}`
}


