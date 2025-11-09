import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * OT（JRDB基準オッズデータ（OT）- 3連複）のフォーマット定義
 * 
 * 
 * レコード長: 4912バイト
 */
export const otFormat: JRDBFormatDefinition = {
  dataType: 'OT',
  description: 'JRDB基準オッズデータ（OT）- 3連複',
  recordLength: 4912,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '登録頭数', start: 9, length: 2, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '登録頭数' },
    { name: '3連複オッズ816', start: 11, length: 6, type: JRDBFieldType.STRING, description: '01-02-03 ～ 最後16-17-18' },
    { name: '予備', start: 4907, length: 4, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 4911, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
