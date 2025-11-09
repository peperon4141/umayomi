import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * SRA（JRDB成績レースデータ（SRA））のフォーマット定義
 * 
 * 
 * レコード長: 1018バイト
 */
export const sraFormat: JRDBFormatDefinition = {
  dataType: 'SRA',
  description: 'JRDB成績レースデータ（SRA）',
  recordLength: 1018,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: 'ハロンタイム', start: 999, length: 18, type: JRDBFieldType.INTEGER_NINE, description: '9 3*18=54BYTE' },
    { name: '1コーナー', start: 63, length: 64, type: JRDBFieldType.STRING, description: '１コーナー' },
    { name: '2コーナー', start: 127, length: 64, type: JRDBFieldType.STRING, description: '２コーナー' },
    { name: '3コーナー', start: 191, length: 64, type: JRDBFieldType.STRING, description: '３コーナー' },
    { name: '4コーナー', start: 255, length: 64, type: JRDBFieldType.STRING, description: '４コーナー' },
    { name: '予備1', start: 319, length: 80, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '予備2', start: 399, length: 8, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 407, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
