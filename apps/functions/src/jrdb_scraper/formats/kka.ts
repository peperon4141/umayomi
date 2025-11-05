import type { JRDBFormatDefinition } from '../parsers/utils'
import { JRDBFieldType } from '../parsers/utils'

/**
 * KKA（JRDB競走馬拡張データ）のフォーマット定義
 * 
 * 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
 * サンプル: https://jrdb.com/program/Kka/KKA020908.txt
 * 
 * 注意: KKAの実際のフォーマットは仕様書を確認して調整が必要です
 */
export const kkaFormat: JRDBFormatDefinition = {
  dataType: 'KKA',
  description: 'JRDB競走馬拡張データ（KKA）',
  recordLength: 200,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  specificationUrl: 'https://jrdb.com/program/Kka/kka_doc.txt',
  sampleUrl: 'https://jrdb.com/program/Kka/KKA020908.txt',
  fields: [
    {
      name: 'レースキー',
      start: 1,
      length: 16,
      type: JRDBFieldType.STRING,
      description: 'レースキー（年月日8桁+場コード2桁+開催回数1桁+日目1桁+レース番号2桁+馬番2桁）'
    },
    {
      name: '拡張データ1',
      start: 17,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ1'
    },
    {
      name: '拡張データ2',
      start: 37,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ2'
    },
    {
      name: '拡張データ3',
      start: 57,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ3'
    },
    {
      name: '拡張データ4',
      start: 77,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ4'
    },
    {
      name: '拡張データ5',
      start: 97,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ5'
    },
    {
      name: '拡張データ6',
      start: 117,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ6'
    },
    {
      name: '拡張データ7',
      start: 137,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ7'
    },
    {
      name: '拡張データ8',
      start: 157,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ8'
    },
    {
      name: '拡張データ9',
      start: 177,
      length: 20,
      type: JRDBFieldType.STRING,
      description: '拡張データ9'
    },
    {
      name: '拡張データ10',
      start: 197,
      length: 4,
      type: JRDBFieldType.STRING,
      description: '拡張データ10'
    }
  ],
  note: 'KKAの実際のフォーマットは仕様書（https://jrdb.com/program/Kka/kka_doc.txt）を確認して調整が必要です'
}

