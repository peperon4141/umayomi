import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * KKA（JRDB拡張競走馬データ（KKA））のフォーマット定義
 * 
 * 
 * レコード長: 324バイト
 */
export const kkaFormat: JRDBFormatDefinition = {
  dataType: 'KKA',
  description: 'JRDB拡張競走馬データ（KKA）',
  recordLength: 324,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '馬番', start: 9, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '馬番' },
    { name: '父馬産駒芝連対率', start: 287, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '※３ 単位％' },
    { name: '父馬産駒ダ連対率', start: 290, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '※３ 単位％' },
    { name: '父馬産駒連対平均距離', start: 293, length: 4, type: JRDBFieldType.INTEGER_NINE, description: '※３' },
    { name: '母父馬産駒芝連対率', start: 297, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '※３ 単位％' },
    { name: '母父馬産駒ダ連対率', start: 300, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '※３ 単位％' },
    { name: '母父馬産駒連対平均距離', start: 303, length: 4, type: JRDBFieldType.INTEGER_NINE, description: '※３' },
    { name: '予備', start: 307, length: 16, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 323, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
