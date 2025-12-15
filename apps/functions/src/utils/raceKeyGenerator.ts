/**
 * JRAレースデータからrace_keyを生成するユーティリティ（Functions用）
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
  if (typeof day === 'number') return day.toString()
  
  // 文字列の場合は小文字に変換（a, b, cなど）
  return day.toString().toLowerCase()
}

/**
 * 開催回数をJRDB形式に変換（1桁の文字列）
 */
export function roundToJRDBFormat(round: number | null | undefined): string {
  if (!round) return '1' // デフォルトは1回
  
  return round.toString() // 1桁のまま
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
 * 年をJRDB形式に変換（2桁の文字列）
 */
export function yearToJRDBFormat(year: number | null | undefined): string {
  if (!year) {
    const now = new Date()
    year = now.getFullYear()
  }
  // 年の下2桁を取得
  return String(year % 100).padStart(2, '0')
}

/**
 * Raceオブジェクトからrace_keyを生成（JRDB仕様に準拠）
 * 形式: 場コード_年_回_日_R
 */
export function generateRaceKey(race: {
  date: Date | any
  racecourse?: string
  venue?: string
  raceNumber: number
  round?: number | null
  day?: string | number | null
}): string {
  // 日付から年を取得
  const date = race.date instanceof Date ? race.date : new Date(race.date)
  const year = date.getFullYear()
  const yearStr = yearToJRDBFormat(year) // 年の下2桁
  
  // 場コード（venueまたはracecourseから取得）
  const venue = race.venue || race.racecourse || '東京'
  const placeCode = venueToPlaceCode(venue)
  
  // 開催回数（デフォルト: 1）
  const round = roundToJRDBFormat(race.round)
  
  // 日目（デフォルト: 1、16進数形式）
  const dayStr = dayToJRDBFormat(race.day)
  
  // レース番号（2桁）
  const raceNumber = raceNumberToJRDBFormat(race.raceNumber)
  
  // race_keyを生成: 場コード_年_回_日_R（JRDB仕様に準拠）
  return `${placeCode}_${yearStr}_${round}_${dayStr}_${raceNumber}`
}

