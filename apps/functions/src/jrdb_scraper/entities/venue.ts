/**
 * JRDB競馬場エンティティ
 * 競馬場名とJRDB場コードのマッピング
 */

/**
 * 競馬場名とJRDB場コードのマッピング
 * JRDBデータファイル（BAC、KYI等）で使用される2桁の場コード
 * 
 * 注意: JRDBコード表（jrdb_code.txt）の「場のコード」セクションは
 *       パドック観察データ（TYB等）用の1桁コードであり、これとは異なります。
 * 
 * 参考: .cursor/rules/JRDB_SPECIFICATIONS.mdc
 */
export const JRDB_VENUE_CODE_MAP: Record<string, string> = {
  '札幌': '01',
  '函館': '02',
  '福島': '03',
  '新潟': '04',
  '東京': '05',
  '中山': '06',
  '中京': '07',
  '京都': '08',
  '阪神': '09',
  '小倉': '10',
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

/**
 * 競馬場名をJRDB場コードに変換
 * @param racecourse - 競馬場名（例: "東京"）
 * @returns JRDB場コード（例: "01"）
 * @throws {Error} 競馬場名が見つからない場合
 */
export function convertRacecourseToJRDBVenueCode(racecourse: string): string {
  const venueCode = JRDB_VENUE_CODE_MAP[racecourse]
  if (!venueCode) throw new Error(`Unknown racecourse: ${racecourse}. Valid racecourses: ${Object.keys(JRDB_VENUE_CODE_MAP).join(', ')}`)
  return venueCode
}

