/**
 * JRAレースデータからrace_keyを生成するユーティリティ
 */

/**
 * 競馬場名をJRDB場コードに変換
 */
export function venueToPlaceCode(venue: string): string {
  const venueMap: { [key: string]: string } = {
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
  return venueMap[venue] || '05' // デフォルトは東京
}

/**
 * 日目をJRDB形式に変換（1, 2, 3, ... → 1, 2, 3, ... / a, b, c, ... → a, b, c, ...）
 */
export function dayToJRDBFormat(day: string | number | null | undefined): string {
  if (!day) return '1' // デフォルトは1日目
  
  // 数値の場合はそのまま文字列に変換
  if (typeof day === 'number') {
    return day.toString()
  }
  
  // 文字列の場合は小文字に変換（a, b, cなど）
  return day.toString().toLowerCase()
}

/**
 * 開催回数をJRDB形式に変換（2桁の文字列）
 */
export function roundToJRDBFormat(round: number | null | undefined): string {
  if (!round) return '05' // デフォルトは5回
  
  return round.toString().padStart(2, '0')
}

/**
 * レース番号をJRDB形式に変換（2桁の文字列）
 */
export function raceNumberToJRDBFormat(raceNumber: number | string | null | undefined): string {
  if (!raceNumber) return '01'
  
  const num = typeof raceNumber === 'string' ? parseInt(raceNumber) : raceNumber
  return num.toString().padStart(2, '0')
}

/**
 * Raceオブジェクトからrace_keyを生成
 */
export function generateRaceKey(race: {
  date: Date | any
  racecourse: string
  raceNumber: number
  round?: number | null
  day?: string | number | null
}): string {
  // 日付をYYYYMMDD形式に変換
  const date = race.date instanceof Date ? race.date : new Date(race.date)
  const dateStr = date.toISOString().split('T')[0].replace(/-/g, '')
  
  // 場コード
  const placeCode = venueToPlaceCode(race.racecourse)
  
  // 開催回数（デフォルト: 05）
  const round = roundToJRDBFormat(race.round)
  
  // 日目（デフォルト: 1）
  const day = dayToJRDBFormat(race.day)
  
  // レース番号
  const raceNumber = raceNumberToJRDBFormat(race.raceNumber)
  
  // race_keyを生成: YYYYMMDD_場コード_回_日_R
  return `${dateStr}_${placeCode}_${round}_${day}_${raceNumber}`
}

