import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * OW（JRDB基準オッズデータ（OW）- ワイド）のフォーマット定義
 * 
 * 
 * レコード長: 780バイト
 */
export const owFormat: JRDBFormatDefinition = {
  dataType: 'OW',
  description: 'JRDB基準オッズデータ（OW）- ワイド',
  recordLength: 780,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '登録頭数', start: 9, length: 2, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '登録頭数' },
    { name: 'ワイドオッズ153', start: 11, length: 5, type: JRDBFieldType.STRING, description: 'オッズ範囲の下側を出力' },
    { name: '予備', start: 776, length: 3, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
    { name: '改行', start: 779, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
