import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * CSA（JRDB調教師データ（CSA））のフォーマット定義
 * 
 * 
 * レコード長: 272バイト
 */
export const csaFormat: JRDBFormatDefinition = {
  dataType: 'CSA',
  description: 'JRDB調教師データ（CSA）',
  recordLength: 272,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '調教師コード', start: 1, length: 5, type: JRDBFieldType.INTEGER_NINE, description: '調教師コード' },
    { name: '登録抹消フラグ', start: 6, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:抹消,0:現役' },
    { name: '登録抹消年月日', start: 7, length: 8, type: JRDBFieldType.INTEGER_NINE, description: 'YYYYMMDD' },
    { name: '調教師名', start: 15, length: 12, type: JRDBFieldType.STRING, description: '全角６文字' },
    { name: '調教師カナ', start: 27, length: 30, type: JRDBFieldType.STRING, description: '全角１５文字' },
    { name: '調教師名略称', start: 57, length: 6, type: JRDBFieldType.STRING, description: '全角３文字' },
    { name: '所属コード', start: 63, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:関東,2:関西,3:他' },
    { name: '所属地域名', start: 64, length: 4, type: JRDBFieldType.STRING, description: '全角２文字、地方の場合' },
    { name: '生年月日', start: 68, length: 8, type: JRDBFieldType.INTEGER_NINE, description: 'YYYYMMDD' },
    { name: '初免許年', start: 76, length: 4, type: JRDBFieldType.INTEGER_NINE, description: 'YYYY' },
    { name: '調教師コメント', start: 80, length: 40, type: JRDBFieldType.STRING, description: 'ＪＲＤＢスタッフの厩舎見解' },
    { name: 'コメント入力年月日', start: 120, length: 8, type: JRDBFieldType.STRING, description: '調教師コメントを入力した年月日' },
    { name: '本年リーディング', start: 128, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '本年リーディング' },
    { name: '本年特別勝数', start: 155, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '本年特別勝数' },
    { name: '本年重賞勝数', start: 158, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '本年重賞勝数' },
    { name: '昨年リーディング', start: 161, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '昨年リーディング' },
    { name: '昨年特別勝数', start: 188, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '昨年特別勝数' },
    { name: '昨年重賞勝数', start: 191, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '昨年重賞勝数' },
    { name: 'データ年月日', start: 234, length: 8, type: JRDBFieldType.INTEGER_NINE, description: 'YYYYMMDD' },
    { name: '予備', start: 242, length: 29, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 271, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
