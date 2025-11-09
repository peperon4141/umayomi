import type { JRDBFormatDefinition } from '../parsers/formatParser'
import { JRDBFieldType } from '../parsers/fieldParser'

/**
 * TYB（JRDB直前情報データ（TYB））のフォーマット定義
 * 
 * 
 * レコード長: 128バイト
 */
export const tybFormat: JRDBFormatDefinition = {
  dataType: 'TYB',
  description: 'JRDB直前情報データ（TYB）',
  recordLength: 128,
  encoding: 'ShiftJIS',
  lineEnding: 'CRLF',
  fields: [
    { name: '場コード', start: 1, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '場コード' },
    { name: '年', start: 3, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '年' },
    { name: '回', start: 5, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '回' },
    { name: '日', start: 6, length: 1, type: JRDBFieldType.STRING_HEX, description: '16進数(数字 or 小文字アルファベット)' },
    { name: 'R', start: 7, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'Ｒ' },
    { name: '馬番', start: 9, length: 2, type: JRDBFieldType.INTEGER_NINE, description: '馬番' },
    { name: 'ＩＤＭ', start: 11, length: 5, type: JRDBFieldType.STRING, description: '前日情報と同じ' },
    { name: '騎手指数', start: 16, length: 5, type: JRDBFieldType.STRING, description: '前日情報と同じ' },
    { name: '情報指数', start: 21, length: 5, type: JRDBFieldType.STRING, description: '前日情報と同じ' },
    { name: 'オッズ指数', start: 26, length: 5, type: JRDBFieldType.STRING, description: 'オッズ指数' },
    { name: 'パドック指数', start: 31, length: 5, type: JRDBFieldType.STRING, description: 'パドック指数' },
    { name: '予備1', start: 36, length: 5, type: JRDBFieldType.STRING, description: '将来拡張用' },
    { name: '総合指数', start: 41, length: 5, type: JRDBFieldType.STRING, description: '総合指数' },
    { name: '馬具変更情報', start: 46, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '0:馬具変更なし' },
    { name: '脚元情報', start: 47, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '0:平行線' },
    { name: '取消フラグ', start: 48, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '取消フラグ' },
    { name: '騎手コード', start: 49, length: 5, type: JRDBFieldType.INTEGER_NINE, description: '騎手マスタリンク用' },
    { name: '騎手名', start: 54, length: 12, type: JRDBFieldType.STRING, description: '全角６文字' },
    { name: '負担重量', start: 66, length: 3, type: JRDBFieldType.INTEGER_NINE, description: '0.1Kg単位' },
    { name: '見習い区分', start: 69, length: 1, type: JRDBFieldType.INTEGER_NINE, description: '1:☆(1K減),2:△(2K減),3:▲(3K減)' },
    { name: '馬場状態コード', start: 70, length: 2, type: JRDBFieldType.INTEGER_NINE, description: 'コード表参照' },
    { name: '天候コード', start: 72, length: 1, type: JRDBFieldType.INTEGER_NINE, description: 'コード表参照' },
    { name: '単勝オッズ', start: 73, length: 6, type: JRDBFieldType.STRING, description: '単勝オッズ（データ作成時点）' },
    { name: '複勝オッズ', start: 79, length: 6, type: JRDBFieldType.STRING, description: '複勝オッズの下側' },
    { name: 'オッズ取得時間', start: 85, length: 4, type: JRDBFieldType.INTEGER_NINE, description: 'HHMM' },
    { name: '馬体重', start: 89, length: 3, type: JRDBFieldType.INTEGER_NINE, description: 'データ無:スペース' },
    { name: '馬体重増減', start: 92, length: 3, type: JRDBFieldType.STRING, description: '符号+数字２桁、データ無:スペース' },
    { name: 'オッズ印', start: 95, length: 1, type: JRDBFieldType.STRING, description: 'オッズ印' },
    { name: 'パドック印', start: 96, length: 1, type: JRDBFieldType.STRING, description: 'パドック印' },
    { name: '直前総合印', start: 97, length: 1, type: JRDBFieldType.STRING, description: '直前総合印' },
    { name: '馬体コード', start: 98, length: 1, type: JRDBFieldType.STRING, description: '第4a版で追加' },
    { name: '気配コード', start: 99, length: 1, type: JRDBFieldType.STRING, description: '第4a版で追加' },
    { name: '発走時間', start: 100, length: 4, type: JRDBFieldType.INTEGER_NINE, description: 'HHMM' },
    { name: '予備', start: 104, length: 23, type: JRDBFieldType.STRING, description: 'スペース' },
    { name: '改行', start: 127, length: 2, type: JRDBFieldType.STRING, description: 'ＣＲ・ＬＦ' },
  ]
}
