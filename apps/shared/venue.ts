/**
 * 競馬場エンティティ
 * 競馬場名とJRDB場コードのマッピング
 */

/**
 * 競馬場名とJRDB場コードのマッピング（JRA用）
 * 注意: JRDBの場コードとは異なる場合があります
 */
export const VENUE_TO_PLACE_CODE_MAP: Record<string, string> = {
  '東京': '05',
  '中山': '06',
  '京都': '07',
  '阪神': '08',
  '新潟': '09',
  '小倉': '10',
  '札幌': '01',
  '函館': '02',
  '福島': '03',
  '中京': '04'
}

/**
 * 場コードから競馬場名への逆マッピング
 */
export const PLACE_CODE_TO_VENUE_MAP: Record<string, string> = {
  '01': '札幌',
  '02': '函館',
  '03': '福島',
  '04': '中京',
  '05': '東京',
  '06': '中山',
  '07': '京都',
  '08': '阪神',
  '09': '新潟',
  '10': '小倉'
}

/**
 * 競馬場名をJRDB場コードに変換
 * @param venue - 競馬場名（例: "東京"）
 * @returns JRDB場コード（例: "05"）
 */
export function venueToPlaceCode(venue: string): string {
  return VENUE_TO_PLACE_CODE_MAP[venue] || '05' // デフォルトは東京
}

/**
 * JRDB場コードを競馬場名に変換
 * @param placeCode - JRDB場コード（例: "05"）
 * @returns 競馬場名（例: "東京"）
 */
export function placeCodeToVenue(placeCode: string): string {
  return PLACE_CODE_TO_VENUE_MAP[placeCode] || placeCode
}

