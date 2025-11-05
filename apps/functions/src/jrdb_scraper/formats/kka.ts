import type { JRDBFormatDefinition } from '../parsers/utils'
import { JRDBFieldType } from '../parsers/utils'

/**
 * KKA（JRDB競走馬拡張データ）のフォーマット定義
 * 
 * 仕様書: https://jrdb.com/program/Kka/kka_doc.txt
 * サンプル: https://jrdb.com/program/Kka/KKA020908.txt
 * 
 * レコード長: 324バイト
 */
export const kkaFormat: JRDBFormatDefinition = {
  dataType: 'KKA',
  description: 'JRDB競走馬拡張データ（KKA）',
  recordLength: 324,
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
      name: 'JRA成績_１着数',
      start: 11,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'JRA成績_１着数'
    },
    {
      name: 'JRA成績_２着数',
      start: 14,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'JRA成績_２着数'
    },
    {
      name: 'JRA成績_３着数',
      start: 17,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'JRA成績_３着数'
    },
    {
      name: 'JRA成績_着外数',
      start: 20,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'JRA成績_着外数'
    },
    {
      name: '交流成績_１着数',
      start: 23,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '交流成績_１着数'
    },
    {
      name: '交流成績_２着数',
      start: 26,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '交流成績_２着数'
    },
    {
      name: '交流成績_３着数',
      start: 29,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '交流成績_３着数'
    },
    {
      name: '交流成績_着外数',
      start: 32,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '交流成績_着外数'
    },
    {
      name: '他成績_１着数',
      start: 35,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '他成績_１着数'
    },
    {
      name: '他成績_２着数',
      start: 38,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '他成績_２着数'
    },
    {
      name: '他成績_３着数',
      start: 41,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '他成績_３着数'
    },
    {
      name: '他成績_着外数',
      start: 44,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '他成績_着外数'
    },
    {
      name: '芝ダ障害別成績_芝_１着数',
      start: 47,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_芝_１着数'
    },
    {
      name: '芝ダ障害別成績_芝_２着数',
      start: 50,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_芝_２着数'
    },
    {
      name: '芝ダ障害別成績_芝_３着数',
      start: 53,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_芝_３着数'
    },
    {
      name: '芝ダ障害別成績_芝_着外数',
      start: 56,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_芝_着外数'
    },
    {
      name: '芝ダ障害別成績_ダ_１着数',
      start: 59,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_ダ_１着数'
    },
    {
      name: '芝ダ障害別成績_ダ_２着数',
      start: 62,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_ダ_２着数'
    },
    {
      name: '芝ダ障害別成績_ダ_３着数',
      start: 65,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_ダ_３着数'
    },
    {
      name: '芝ダ障害別成績_ダ_着外数',
      start: 68,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_ダ_着外数'
    },
    {
      name: '芝ダ障害別成績_障_１着数',
      start: 71,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_障_１着数'
    },
    {
      name: '芝ダ障害別成績_障_２着数',
      start: 74,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_障_２着数'
    },
    {
      name: '芝ダ障害別成績_障_３着数',
      start: 77,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_障_３着数'
    },
    {
      name: '芝ダ障害別成績_障_着外数',
      start: 80,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別成績_障_着外数'
    },
    {
      name: '芝ダ障害別距離成績_芝_１着数',
      start: 83,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_芝_１着数'
    },
    {
      name: '芝ダ障害別距離成績_芝_２着数',
      start: 86,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_芝_２着数'
    },
    {
      name: '芝ダ障害別距離成績_芝_３着数',
      start: 89,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_芝_３着数'
    },
    {
      name: '芝ダ障害別距離成績_芝_着外数',
      start: 92,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_芝_着外数'
    },
    {
      name: '芝ダ障害別距離成績_ダ_１着数',
      start: 95,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_ダ_１着数'
    },
    {
      name: '芝ダ障害別距離成績_ダ_２着数',
      start: 98,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_ダ_２着数'
    },
    {
      name: '芝ダ障害別距離成績_ダ_３着数',
      start: 101,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_ダ_３着数'
    },
    {
      name: '芝ダ障害別距離成績_ダ_着外数',
      start: 104,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '芝ダ障害別距離成績_ダ_着外数'
    },
    {
      name: 'トラック距離成績_１着数',
      start: 107,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'トラック距離成績_１着数'
    },
    {
      name: 'トラック距離成績_２着数',
      start: 110,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'トラック距離成績_２着数'
    },
    {
      name: 'トラック距離成績_３着数',
      start: 113,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'トラック距離成績_３着数'
    },
    {
      name: 'トラック距離成績_着外数',
      start: 116,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'トラック距離成績_着外数'
    },
    {
      name: 'ローテ成績_１着数',
      start: 119,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'ローテ成績_１着数'
    },
    {
      name: 'ローテ成績_２着数',
      start: 122,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'ローテ成績_２着数'
    },
    {
      name: 'ローテ成績_３着数',
      start: 125,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'ローテ成績_３着数'
    },
    {
      name: 'ローテ成績_着外数',
      start: 128,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'ローテ成績_着外数'
    },
    {
      name: '回り成績_１着数',
      start: 131,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '回り成績_１着数'
    },
    {
      name: '回り成績_２着数',
      start: 134,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '回り成績_２着数'
    },
    {
      name: '回り成績_３着数',
      start: 137,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '回り成績_３着数'
    },
    {
      name: '回り成績_着外数',
      start: 140,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '回り成績_着外数'
    },
    {
      name: '騎手成績_１着数',
      start: 143,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手成績_１着数'
    },
    {
      name: '騎手成績_２着数',
      start: 146,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手成績_２着数'
    },
    {
      name: '騎手成績_３着数',
      start: 149,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手成績_３着数'
    },
    {
      name: '騎手成績_着外数',
      start: 152,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手成績_着外数'
    },
    {
      name: '良成績_芝_１着数',
      start: 155,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_芝_１着数'
    },
    {
      name: '良成績_芝_２着数',
      start: 158,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_芝_２着数'
    },
    {
      name: '良成績_芝_３着数',
      start: 161,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_芝_３着数'
    },
    {
      name: '良成績_芝_着外数',
      start: 164,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_芝_着外数'
    },
    {
      name: '良成績_ダ_１着数',
      start: 167,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_ダ_１着数'
    },
    {
      name: '良成績_ダ_２着数',
      start: 170,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_ダ_２着数'
    },
    {
      name: '良成績_ダ_３着数',
      start: 173,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_ダ_３着数'
    },
    {
      name: '良成績_ダ_着外数',
      start: 176,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '良成績_ダ_着外数'
    },
    {
      name: '稍成績_芝_１着数',
      start: 179,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_芝_１着数'
    },
    {
      name: '稍成績_芝_２着数',
      start: 182,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_芝_２着数'
    },
    {
      name: '稍成績_芝_３着数',
      start: 185,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_芝_３着数'
    },
    {
      name: '稍成績_芝_着外数',
      start: 188,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_芝_着外数'
    },
    {
      name: '稍成績_ダ_１着数',
      start: 191,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_ダ_１着数'
    },
    {
      name: '稍成績_ダ_２着数',
      start: 194,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_ダ_２着数'
    },
    {
      name: '稍成績_ダ_３着数',
      start: 197,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_ダ_３着数'
    },
    {
      name: '稍成績_ダ_着外数',
      start: 200,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '稍成績_ダ_着外数'
    },
    {
      name: '重成績_芝_１着数',
      start: 203,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_芝_１着数'
    },
    {
      name: '重成績_芝_２着数',
      start: 206,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_芝_２着数'
    },
    {
      name: '重成績_芝_３着数',
      start: 209,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_芝_３着数'
    },
    {
      name: '重成績_芝_着外数',
      start: 212,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_芝_着外数'
    },
    {
      name: '重成績_ダ_１着数',
      start: 215,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_ダ_１着数'
    },
    {
      name: '重成績_ダ_２着数',
      start: 218,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_ダ_２着数'
    },
    {
      name: '重成績_ダ_３着数',
      start: 221,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_ダ_３着数'
    },
    {
      name: '重成績_ダ_着外数',
      start: 224,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '重成績_ダ_着外数'
    },
    {
      name: 'Sペース成績_１着数',
      start: 227,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Sペース成績_１着数'
    },
    {
      name: 'Sペース成績_２着数',
      start: 230,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Sペース成績_２着数'
    },
    {
      name: 'Sペース成績_３着数',
      start: 233,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Sペース成績_３着数'
    },
    {
      name: 'Sペース成績_着外数',
      start: 236,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Sペース成績_着外数'
    },
    {
      name: 'Mペース成績_１着数',
      start: 239,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Mペース成績_１着数'
    },
    {
      name: 'Mペース成績_２着数',
      start: 242,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Mペース成績_２着数'
    },
    {
      name: 'Mペース成績_３着数',
      start: 245,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Mペース成績_３着数'
    },
    {
      name: 'Mペース成績_着外数',
      start: 248,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Mペース成績_着外数'
    },
    {
      name: 'Hペース成績_１着数',
      start: 251,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Hペース成績_１着数'
    },
    {
      name: 'Hペース成績_２着数',
      start: 254,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Hペース成績_２着数'
    },
    {
      name: 'Hペース成績_３着数',
      start: 257,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Hペース成績_３着数'
    },
    {
      name: 'Hペース成績_着外数',
      start: 260,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: 'Hペース成績_着外数'
    },
    {
      name: '季節成績_１着数',
      start: 263,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '季節成績_１着数'
    },
    {
      name: '季節成績_２着数',
      start: 266,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '季節成績_２着数'
    },
    {
      name: '季節成績_３着数',
      start: 269,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '季節成績_３着数'
    },
    {
      name: '季節成績_着外数',
      start: 272,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '季節成績_着外数'
    },
    {
      name: '枠成績_１着数',
      start: 275,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '枠成績_１着数'
    },
    {
      name: '枠成績_２着数',
      start: 278,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '枠成績_２着数'
    },
    {
      name: '枠成績_３着数',
      start: 281,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '枠成績_３着数'
    },
    {
      name: '枠成績_着外数',
      start: 284,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '枠成績_着外数'
    },
    {
      name: '騎手距離成績_１着数',
      start: 215,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手距離成績_１着数'
    },
    {
      name: '騎手距離成績_２着数',
      start: 218,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手距離成績_２着数'
    },
    {
      name: '騎手距離成績_３着数',
      start: 221,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手距離成績_３着数'
    },
    {
      name: '騎手距離成績_着外数',
      start: 224,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手距離成績_着外数'
    },
    {
      name: '騎手トラック距離成績_１着数',
      start: 227,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手トラック距離成績_１着数'
    },
    {
      name: '騎手トラック距離成績_２着数',
      start: 230,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手トラック距離成績_２着数'
    },
    {
      name: '騎手トラック距離成績_３着数',
      start: 233,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手トラック距離成績_３着数'
    },
    {
      name: '騎手トラック距離成績_着外数',
      start: 236,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手トラック距離成績_着外数'
    },
    {
      name: '騎手調教師別成績_１着数',
      start: 239,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手調教師別成績_１着数'
    },
    {
      name: '騎手調教師別成績_２着数',
      start: 242,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手調教師別成績_２着数'
    },
    {
      name: '騎手調教師別成績_３着数',
      start: 245,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手調教師別成績_３着数'
    },
    {
      name: '騎手調教師別成績_着外数',
      start: 248,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手調教師別成績_着外数'
    },
    {
      name: '騎手馬主別成績_１着数',
      start: 251,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手馬主別成績_１着数'
    },
    {
      name: '騎手馬主別成績_２着数',
      start: 254,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手馬主別成績_２着数'
    },
    {
      name: '騎手馬主別成績_３着数',
      start: 257,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手馬主別成績_３着数'
    },
    {
      name: '騎手馬主別成績_着外数',
      start: 260,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手馬主別成績_着外数'
    },
    {
      name: '騎手ブリンカ成績_１着数',
      start: 263,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手ブリンカ成績_１着数'
    },
    {
      name: '騎手ブリンカ成績_２着数',
      start: 266,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手ブリンカ成績_２着数'
    },
    {
      name: '騎手ブリンカ成績_３着数',
      start: 269,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手ブリンカ成績_３着数'
    },
    {
      name: '騎手ブリンカ成績_着外数',
      start: 272,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '騎手ブリンカ成績_着外数'
    },
    {
      name: '調教師馬主別成績_１着数',
      start: 275,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '調教師馬主別成績_１着数'
    },
    {
      name: '調教師馬主別成績_２着数',
      start: 278,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '調教師馬主別成績_２着数'
    },
    {
      name: '調教師馬主別成績_３着数',
      start: 281,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '調教師馬主別成績_３着数'
    },
    {
      name: '調教師馬主別成績_着外数',
      start: 284,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '調教師馬主別成績_着外数'
    },
    {
      name: '父馬産駒芝連対率',
      start: 287,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '父馬産駒芝連対率（単位％）'
    },
    {
      name: '父馬産駒ダ連対率',
      start: 290,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '父馬産駒ダ連対率（単位％）'
    },
    {
      name: '父馬産駒連対平均距離',
      start: 293,
      length: 4,
      type: JRDBFieldType.INTEGER,
      description: '父馬産駒連対平均距離'
    },
    {
      name: '母父馬産駒芝連対率',
      start: 297,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '母父馬産駒芝連対率（単位％）'
    },
    {
      name: '母父馬産駒ダ連対率',
      start: 300,
      length: 3,
      type: JRDBFieldType.INTEGER,
      description: '母父馬産駒ダ連対率（単位％）'
    },
    {
      name: '母父馬産駒連対平均距離',
      start: 303,
      length: 4,
      type: JRDBFieldType.INTEGER,
      description: '母父馬産駒連対平均距離'
    }
    // 注意: 予備 16 X 307（307-322バイト）と改行 2 X 323（323-324バイト）はパース対象外
  ]
}
