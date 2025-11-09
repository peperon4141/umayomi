import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * HJC（JRDB払戻情報データ（HJC））のフォーマット定義
 * 
 * 
 * レコード長: 444バイト
 */
export const hjcFormat: JRDBFormatDefinition = {
  dataType: 'HJC',
  description: 'JRDB払戻情報データ（HJC）',
  recordLength: 444,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '単勝払戻', start: 9, length: 3, type: JRDBFieldType.INTEGER_NINE, description: '* 3 = 27 BYTE' },
    { name: '複勝払戻', start: 9, length: 5, type: JRDBFieldType.INTEGER_NINE, description: '* 5 = 45 BYTE' },
    { name: '枠連払戻', start: 9, length: 3, type: JRDBFieldType.INTEGER_NINE, description: '* 3 = 27 BYTE' },
    { name: '馬連払戻', start: 12, length: 3, type: JRDBFieldType.INTEGER_NINE, description: '* 3 = 36 BYTE' },
    { name: 'ワイド払戻', start: 12, length: 7, type: JRDBFieldType.INTEGER_NINE, description: '* 7 = 84 BYTE' },
    { name: '馬単払戻', start: 12, length: 6, type: JRDBFieldType.INTEGER_NINE, description: '* 6 = 72 BYTE' },
    { name: '3連複払戻', start: 14, length: 3, type: JRDBFieldType.INTEGER_NINE, description: '* 3 = 42 BYTE' },
    { name: '3連単払戻', start: 15, length: 6, type: JRDBFieldType.INTEGER_NINE, description: '* 6 = 90 BYTE' },
    { name: '予備1', start: 432, length: 10, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '予備2', start: 442, length: 1, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 443, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
