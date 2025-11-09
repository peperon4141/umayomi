import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * SRB（JRDB成績レースデータ（SRB））のフォーマット定義
 * 
 * 
 * レコード長: 1018バイト
 */
export const srbFormat: JRDBFormatDefinition = {
  dataType: 'SRB',
  description: 'JRDB成績レースデータ（SRB）',
  recordLength: 1018,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '日' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: 'ハロンタイム', start: 999, length: 18, type: JRDBFieldType.INTEGER_NINE, description: '9 3*18=54BYTE' },
    { name: '1コーナー', start: 63, length: 64, type: JRDBFieldType.STRING, description: '１コーナー' },
    { name: '2コーナー', start: 127, length: 64, type: JRDBFieldType.STRING, description: '２コーナー' },
    { name: '3コーナー', start: 191, length: 64, type: JRDBFieldType.STRING, description: '３コーナー' },
    { name: '4コーナー', start: 255, length: 64, type: JRDBFieldType.STRING, description: '４コーナー' },
    { name: 'ペースアップ位置', start: 319, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '残りハロン数' },
    { name: '1角', start: 321, length: 3, type: JRDBFieldType.STRING, description: '（内、中、外）' },
    { name: '2角', start: 324, length: 3, type: JRDBFieldType.STRING, description: '（内、中、外）' },
    { name: '向正', start: 327, length: 3, type: JRDBFieldType.STRING, description: '（内、中、外）' },
    { name: '3角', start: 330, length: 3, type: JRDBFieldType.STRING, description: '（内、中、外）' },
    { name: '4角', start: 333, length: 5, type: JRDBFieldType.STRING, description: '（最内、内、中、外、大外）' },
    { name: '直線', start: 338, length: 5, type: JRDBFieldType.STRING, description: '（最内、内、中、外、大外）' },
    { name: 'レースコメント', start: 343, length: 500, type: JRDBFieldType.STRING, description: 'レースコメント' },
    { name: '予備', start: 843, length: 8, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 851, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
