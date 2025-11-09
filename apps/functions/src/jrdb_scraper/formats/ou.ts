import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * OU（JRDB基準オッズデータ（OU）- 馬単）のフォーマット定義
 * 
 * 
 * レコード長: 1856バイト
 */
export const ouFormat: JRDBFormatDefinition = {
  dataType: 'OU',
  description: 'JRDB基準オッズデータ（OU）- 馬単',
  recordLength: 1856,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '登録頭数', start: 9, length: 2, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '登録頭数' },
    { name: '馬単オッズ306', start: 11, length: 6, type: JRDBFieldType.STRING, description: '馬単オッズ 306' },
    { name: '予備', start: 1847, length: 8, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 1855, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
