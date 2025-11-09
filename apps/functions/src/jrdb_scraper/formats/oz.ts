import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * OZ（JRDB基準オッズデータ（OZ）- 単勝・複勝・連勝）のフォーマット定義
 * 
 * 
 * レコード長: 957バイト
 */
export const ozFormat: JRDBFormatDefinition = {
  dataType: 'OZ',
  description: 'JRDB基準オッズデータ（OZ）- 単勝・複勝・連勝',
  recordLength: 957,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '登録頭数', start: 9, length: 2, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '登録頭数' },
    { name: '単勝オッズ18', start: 11, length: 5, type: JRDBFieldType.STRING, description: '単勝オッズ 18' },
    { name: '複勝オッズ18', start: 101, length: 5, type: JRDBFieldType.STRING, description: '複勝オッズ 18' },
    { name: '連勝オッズ153', start: 191, length: 5, type: JRDBFieldType.STRING, description: '連勝オッズ 153' },
    { name: '改行', start: 956, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
