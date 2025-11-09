import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * OV（JRDB基準オッズデータ（OV）- 3連単）のフォーマット定義
 * 
 * 
 * レコード長: 34288バイト
 */
export const ovFormat: JRDBFormatDefinition = {
  dataType: 'OV',
  description: 'JRDB基準オッズデータ（OV）- 3連単',
  recordLength: 34288,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '登録頭数', start: 9, length: 2, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '登録頭数' },
    { name: '3連単オッズ4896', start: 11, length: 7, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '0.1倍単位※1' },
    { name: '予備', start: 34283, length: 4, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 34287, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
