import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * JOA（JRDB情報データ（JOA））のフォーマット定義
 * 
 * 
 * レコード長: 116バイト
 */
export const joaFormat: JRDBFormatDefinition = {
  dataType: 'JOA',
  description: 'JRDB情報データ（JOA）',
  recordLength: 116,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: '馬番', start: 9, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '馬番' },
    { name: '血統登録番号', start: 11, length: 8, type: JRDBFieldType.STRING, description: '血統登録番号' },
    { name: '馬名', start: 19, length: 36, type: JRDBFieldType.STRING, description: '全角１８文字' },
    { name: '基準オッズ', start: 55, length: 5, type: JRDBFieldType.STRING, description: '基準オッズ' },
    { name: '基準複勝オッズ', start: 60, length: 5, type: JRDBFieldType.STRING, description: '基準複勝オッズ' },
    { name: 'CID調教素点', start: 65, length: 5, type: JRDBFieldType.STRING, description: 'CID調教素点' },
    { name: 'CID厩舎素点', start: 70, length: 5, type: JRDBFieldType.STRING, description: 'CID厩舎素点' },
    { name: 'CID素点', start: 75, length: 5, type: JRDBFieldType.STRING, description: 'CID素点' },
    { name: 'CID', start: 80, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: 'CID' },
    { name: 'LS指数', start: 83, length: 5, type: JRDBFieldType.STRING, description: 'LS指数' },
    { name: 'LS評価', start: 88, length: 1, type: JRDBFieldType.STRING, description: 'A,B,C のランクに分類' },
    { name: 'EM', start: 89, length: 1, type: JRDBFieldType.STRING, description: '1:消し,それ以外スペース' },
    { name: '厩舎ＢＢ印', start: 90, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '厩舎ＢＢの印, 印コード参照' },
    { name: '厩舎ＢＢ◎単勝回収率', start: 91, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '厩舎ＢＢが該当する厩舎の馬に◎' },
    { name: '厩舎ＢＢ◎連対率', start: 96, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '厩舎ＢＢが該当する厩舎の馬に◎' },
    { name: '騎手ＢＢ印', start: 101, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '騎手ＢＢの印' },
    { name: '騎手ＢＢ◎単勝回収率', start: 102, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '騎手ＢＢが該当する厩舎の馬に◎' },
    { name: '騎手ＢＢ◎連対率', start: 107, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '騎手ＢＢが該当する厩舎の馬に◎' },
    { name: '予備', start: 112, length: 3, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 115, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
