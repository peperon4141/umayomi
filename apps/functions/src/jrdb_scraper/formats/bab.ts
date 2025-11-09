import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * BAB（JRDB番組データ（BAB））のフォーマット定義
 * 
 * 
 * レコード長: 168バイト
 */
export const babFormat: JRDBFormatDefinition = {
  dataType: 'BAB',
  description: 'JRDB番組データ（BAB）',
  recordLength: 168,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '年月日', start: 9, length: 8, type: JRDBFieldType.INTEGER_NINE, description: 'YYYYMMDD' },
    { name: '発走時間', start: 17, length: 4, type: JRDBFieldType.STRING, description: 'HHMM' },
    { name: '距離', start: 21, length: 4, type: JRDBFieldType.INTEGER_NINE, description: '距離' },
    { name: '芝ダ障害コード', start: 25, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:芝, 2:ダート, 3:障害' },
    { name: '右左', start: 26, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:右, 2:左, 3:直, 9:他' },
    { name: '内外', start: 27, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:通常(内), 2:外, 3,直ダ, 9:他' },
    { name: '種別', start: 28, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '４歳以上等、→JRDBデータコード表' },
    { name: '条件', start: 30, length: 2, type: JRDBFieldType.STRING, description: '900万下等、 →JRDBデータコード表' },
    { name: '記号', start: 32, length: 3, type: JRDBFieldType.INTEGER_NINE, description: '○混等、 →JRDBデータコード表' },
    { name: '重量', start: 35, length: 1, type: JRDBFieldType.INTEGER_NINE, description: 'ハンデ等、 →JRDBデータコード表' },
    { name: 'グレード', start: 36, length: 1, type: JRDBFieldType.INTEGER_NINE, description: 'Ｇ１等 →JRDBデータコード表' },
    { name: 'レース名', start: 37, length: 50, type: JRDBFieldType.STRING, description: 'レース名の通称（全角２５文字）' },
    { name: '回数', start: 87, length: 8, type: JRDBFieldType.STRING, description: '第＿回' },
    { name: '頭数', start: 95, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '頭数' },
    { name: 'コース', start: 97, length: 1, type: JRDBFieldType.STRING, description: '1:A, 2:A1, 3:A2, 4:B, 5:C, 6:D' },
    { name: '開催区分', start: 98, length: 1, type: JRDBFieldType.STRING, description: '1:関東, 2:関西, 3:ローカル' },
    { name: 'レース名短縮', start: 99, length: 8, type: JRDBFieldType.STRING, description: '全角４文字' },
    { name: 'レース名9文字', start: 107, length: 18, type: JRDBFieldType.STRING, description: '全角９文字' },
    { name: 'データ区分', start: 125, length: 1, type: JRDBFieldType.STRING, description: '1:特別登録, 2:想定確定, 3:前日' },
    { name: '1着賞金', start: 126, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '2着賞金', start: 131, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '3着賞金', start: 136, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '4着賞金', start: 141, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '5着賞金', start: 146, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '1着算入賞金', start: 151, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '2着算入賞金', start: 156, length: 5, type: JRDBFieldType.INTEGER_ZERO_BLANK, description: '単位（万円）' },
    { name: '予備', start: 161, length: 6, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 167, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
