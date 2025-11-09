import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * KSA（JRDB騎手データ（KSA））のフォーマット定義
 * 
 * 
 * レコード長: 272バイト
 */
export const ksaFormat: JRDBFormatDefinition = {
  dataType: 'KSA',
  description: 'JRDB騎手データ（KSA）',
  recordLength: 272,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '騎手コード', start: 1, length: 5, type: JRDBFieldType.INTEGER_NINE, description: '騎手コード' },
    { name: '登録抹消フラグ', start: 6, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:抹消,0:現役' },
    { name: '登録抹消年月日', start: 7, length: 8, type: JRDBFieldType.INTEGER_NINE, description: 'YYYYMMDD' },
    { name: '騎手名', start: 15, length: 12, type: JRDBFieldType.STRING, description: '全角６文字' },
    { name: '騎手カナ', start: 27, length: 30, type: JRDBFieldType.STRING, description: '全角１５文字' },
    { name: '騎手名略称', start: 57, length: 6, type: JRDBFieldType.STRING, description: '全角３文字' },
    { name: '所属コード', start: 63, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:関東,2:関西,3:他' },
    { name: '所属地域名', start: 64, length: 4, type: JRDBFieldType.STRING, description: '全角２文字、地方の場合' },
    { name: '生年月日', start: 68, length: 8, type: JRDBFieldType.INTEGER_NINE, description: 'YYYYMMDD' },
    { name: '初免許年', start: 76, length: 4, type: JRDBFieldType.INTEGER_NINE, description: 'YYYY' },
    { name: '見習い区分', start: 80, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:☆(1K減),2:△(2K),3:▲(3K)' },
    { name: '所属厩舎', start: 81, length: 5, type: JRDBFieldType.INTEGER_NINE, description: '所属厩舎の調教師コード' },
    { name: '騎手コメント', start: 86, length: 40, type: JRDBFieldType.STRING, description: 'ＪＲＤＢスタッフの騎手評価' },
    { name: 'コメント入力年月日', start: 126, length: 8, type: JRDBFieldType.STRING, description: '騎手コメントを入力した年月日' },
    { name: '本年リーディング', start: 134, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '本年リーディング' },
    { name: '本年特別勝数', start: 161, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '本年特別勝数' },
    { name: '本年重賞勝数', start: 164, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '本年重賞勝数' },
    { name: '昨年リーディング', start: 167, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '昨年リーディング' },
    { name: '昨年特別勝数', start: 194, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '昨年特別勝数' },
    { name: '昨年重賞勝数', start: 197, length: 3, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '昨年重賞勝数' },
    { name: 'データ年月日', start: 240, length: 8, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '予備', start: 248, length: 23, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 271, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
