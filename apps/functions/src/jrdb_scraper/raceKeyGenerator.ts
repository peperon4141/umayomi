/**
 * JRDBレースキー生成ユーティリティ
 * JRDBのレースキーは以下の形式：
 * 開催日（YYYYMMDD）+ 場コード（2桁）+ 開催回数（1桁）+ 日目（1桁）+ レース番号（2桁）
 */

/**
 * 競馬場名をJRDB場コードに変換
 */
export function convertRacecourseToJRDBVenueCode(racecourse: string): string {
  const venueMap: Record<string, string> = {
    '東京': '01',
    '中山': '02',
    '京都': '03',
    '阪神': '04',
    '新潟': '05',
    '小倉': '06',
    '福島': '07',
    '中京': '08',
    '札幌': '09',
    '函館': '10',
    '門別': '12',
    '盛岡': '13',
    '水沢': '14',
    '金沢': '15',
    '川崎': '16',
    '船橋': '17',
    '大井': '18',
    '浦和': '19',
    '名古屋': '20',
    '園田': '22',
    '姫路': '23',
    '高知': '24',
    '佐賀': '25',
    '荒尾': '26',
    '中津': '27',
    '北九州': '28',
  }
  return venueMap[racecourse] || '01'
}

/**
 * レースキーを生成
 * @param year - 年（例: 2025）
 * @param month - 月（例: 11）
 * @param day - 日（例: 2）
 * @param racecourse - 競馬場名（例: "東京"）
 * @param kaisaiRound - 開催回数（例: 1）
 * @param kaisaiDay - 日目（例: 1）
 * @param raceNumber - レース番号（例: 11）
 * @returns JRDBレースキー（例: "2025110201011"）
 */
export function generateJRDBRaceKey(
  year: number,
  month: number,
  day: number,
  racecourse: string,
  kaisaiRound: number,
  kaisaiDay: number,
  raceNumber: number
): string {
  const dateFormatted = `${year}${String(month).padStart(2, '0')}${String(day).padStart(2, '0')}`
  const venueCode = convertRacecourseToJRDBVenueCode(racecourse)
  const roundStr = String(kaisaiRound)
  const dayStr = String(kaisaiDay)
  const raceNumStr = String(raceNumber).padStart(2, '0')
  
  return `${dateFormatted}${venueCode}${roundStr}${dayStr}${raceNumStr}`
}

/**
 * 2025-11-02 東京 11レース用のレースキー生成
 * 開催回数と日目は暫定的に1とする
 */
export function generateSampleRaceKey(): string {
  return generateJRDBRaceKey(2025, 11, 2, '東京', 1, 1, 11)
}

/**
 * JRDBデータファイルURLを生成
 * @param dataType - データ種別（例: 'KYI', 'KYH', 'KYG', 'KKA'）
 * @param date - 日付（YYMMDD形式、例: "251102" = 2025年11月02日）
 * @returns JRDBメンバーページのURL
 * 
 * 注意: 実際のURL形式はJRDBのメンバーページ構造に依存します。
 * メンバーページのHTMLからリンクを取得する必要がある可能性があります。
 */
export function generateJRDBDataFileUrl(dataType: string, date: string): string {
  // データ種別コードを大文字小文字混在形式に変換（例: KYI -> Kyi, KKA -> Kka）
  const dataTypeCode = dataType.charAt(0).toUpperCase() + dataType.substring(1).toLowerCase()
  const fileName = `${dataType}${date}.lzh`
  
  // メンバーページのURLから直接ファイルをダウンロードする場合のURL形式
  // TODO: 実際のURL形式を確認し、必要に応じてメンバーページのHTMLからリンクを取得する処理を実装
  // 例: https://jrdb.com/member/data/{dataTypeCode}/{fileName}
  return `https://jrdb.com/member/data/${dataTypeCode}/${fileName}`
}

/**
 * KY系データの全種類を取得
 */
import { JRDBDataType } from '../../../shared/src/jrdb'

export function getKYDataTypes(): JRDBDataType[] {
  return [JRDBDataType.KYI, JRDBDataType.KYH, JRDBDataType.KYG, JRDBDataType.KKA]
}

