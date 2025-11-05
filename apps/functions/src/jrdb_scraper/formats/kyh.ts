import type { JRDBFormatDefinition } from '../parsers/utils'
import { JRDBFieldType } from '../parsers/utils'

/**
 * KYH（JRDB競走馬データ - 標準版）のフォーマット定義
 * 
 * 仕様書: https://jrdb.com/program/Kyh/kyh_doc.txt
 * 使用説明: https://jrdb.com/program/Kyh/ky_siyo_doc.txt
 * サンプル: https://jrdb.com/program/Kyh/KYH080913.txt
 */
export const kyhFormat: JRDBFormatDefinition = {
  dataType: 'KYH',
  description: 'JRDB競走馬データ（KYH）- 標準版',
  recordLength: 545,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  specificationUrl: 'https://jrdb.com/program/Kyh/kyh_doc.txt',
  usageGuideUrl: 'https://jrdb.com/program/Kyh/ky_siyo_doc.txt',
  sampleUrl: 'https://jrdb.com/program/Kyh/KYH080913.txt',
  fields: [
    {
      name: 'レースキー',
      start: 1,
      length: 16,
      type: JRDBFieldType.STRING,
      description: 'レースキー（年月日8桁+場コード2桁+開催回数1桁+日目1桁+レース番号2桁+馬番2桁）'
    },
    {
      name: 'IDM',
      start: 17,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: 'IDM（インデックス）'
    },
    {
      name: '情報コード',
      start: 23,
      length: 2,
      type: JRDBFieldType.STRING,
      description: '情報コード'
    },
    {
      name: '総合指数',
      start: 25,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '総合指数'
    },
    {
      name: 'パドック指数',
      start: 31,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: 'パドック指数'
    },
    {
      name: '直前指数',
      start: 37,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '直前指数'
    },
    {
      name: '芝適性',
      start: 43,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '芝適性'
    },
    {
      name: 'ダート適性',
      start: 49,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: 'ダート適性'
    },
    {
      name: '距離適性',
      start: 55,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '距離適性'
    },
    {
      name: 'クラス指数',
      start: 61,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: 'クラス指数'
    },
    {
      name: 'ペース指数',
      start: 67,
      length: 4,
      type: JRDBFieldType.INTEGER,
      description: 'ペース指数'
    },
    {
      name: '上がり指数',
      start: 71,
      length: 2,
      type: JRDBFieldType.INTEGER,
      description: '上がり指数'
    },
    {
      name: '位置指数',
      start: 73,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '位置指数'
    },
    {
      name: 'ペース指数2',
      start: 79,
      length: 4,
      type: JRDBFieldType.INTEGER,
      description: 'ペース指数2'
    },
    {
      name: '上がり指数2',
      start: 83,
      length: 2,
      type: JRDBFieldType.INTEGER,
      description: '上がり指数2'
    },
    {
      name: '逃げ指数',
      start: 85,
      length: 2,
      type: JRDBFieldType.INTEGER,
      description: '逃げ指数'
    },
    {
      name: '先行指数',
      start: 87,
      length: 2,
      type: JRDBFieldType.INTEGER,
      description: '先行指数'
    },
    {
      name: '差し指数',
      start: 89,
      length: 2,
      type: JRDBFieldType.INTEGER,
      description: '差し指数'
    },
    {
      name: '追込指数',
      start: 91,
      length: 2,
      type: JRDBFieldType.INTEGER,
      description: '追込指数'
    },
    {
      name: 'ペース指数3',
      start: 93,
      length: 4,
      type: JRDBFieldType.INTEGER,
      description: 'ペース指数3'
    },
    {
      name: '位置指数2',
      start: 97,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '位置指数2'
    },
    {
      name: 'クラス指数2',
      start: 103,
      length: 4,
      type: JRDBFieldType.INTEGER,
      description: 'クラス指数2'
    },
    {
      name: '速度指数',
      start: 107,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '速度指数'
    },
    {
      name: '馬場指数',
      start: 113,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '馬場指数'
    },
    {
      name: '距離指数',
      start: 119,
      length: 6,
      type: JRDBFieldType.FLOAT,
      description: '距離指数'
    },
    {
      name: '騎手コード',
      start: 125,
      length: 4,
      type: JRDBFieldType.STRING,
      description: '騎手コード'
    },
    {
      name: '騎手名',
      start: 129,
      length: 8,
      type: JRDBFieldType.STRING,
      description: '騎手名（全角8文字）'
    },
    {
      name: '調教師コード',
      start: 137,
      length: 4,
      type: JRDBFieldType.STRING,
      description: '調教師コード'
    },
    {
      name: '調教師名',
      start: 141,
      length: 8,
      type: JRDBFieldType.STRING,
      description: '調教師名（全角8文字）'
    },
    {
      name: '所属',
      start: 149,
      length: 4,
      type: JRDBFieldType.STRING,
      description: '所属（美浦/栗東）'
    },
    {
      name: '血統登録番号',
      start: 153,
      length: 8,
      type: JRDBFieldType.STRING,
      description: '血統登録番号'
    },
    {
      name: '前走競走成績キー1',
      start: 161,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '前走競走成績キー1'
    },
    {
      name: '前走競走成績キー2',
      start: 177,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '前走競走成績キー2'
    },
    {
      name: '前走競走成績キー3',
      start: 193,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '前走競走成績キー3'
    },
    {
      name: '前走競走成績キー4',
      start: 209,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '前走競走成績キー4'
    },
    {
      name: '前走競走成績キー5',
      start: 225,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '前走競走成績キー5'
    },
    {
      name: '調教タイム1',
      start: 241,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム1（MMDDHHMM形式など）'
    },
    {
      name: '調教タイム2',
      start: 257,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム2'
    },
    {
      name: '調教タイム3',
      start: 273,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム3'
    },
    {
      name: '調教タイム4',
      start: 289,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム4'
    },
    {
      name: '調教タイム5',
      start: 305,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム5'
    },
    {
      name: '調教タイム6',
      start: 321,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム6'
    },
    {
      name: '調教タイム7',
      start: 337,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム7'
    },
    {
      name: '調教タイム8',
      start: 353,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム8'
    },
    {
      name: '調教タイム9',
      start: 369,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム9'
    },
    {
      name: '調教タイム10',
      start: 385,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム10'
    },
    {
      name: '調教タイム11',
      start: 401,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム11'
    },
    {
      name: '調教タイム12',
      start: 417,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム12'
    },
    {
      name: '調教タイム13',
      start: 433,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム13'
    },
    {
      name: '調教タイム14',
      start: 449,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム14'
    },
    {
      name: '調教タイム15',
      start: 465,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム15'
    },
    {
      name: '調教タイム16',
      start: 481,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム16'
    },
    {
      name: '調教タイム17',
      start: 497,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム17'
    },
    {
      name: '調教タイム18',
      start: 513,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム18'
    },
    {
      name: '調教タイム19',
      start: 529,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム19'
    },
    {
      name: '調教タイム20',
      start: 545,
      length: 16,
      type: JRDBFieldType.STRING,
      description: '調教タイム20'
    }
  ]
}

