/**
 * JRAレースデータからrace_keyを生成するユーティリティ
 */

/**
 * 競馬場名をJRDB場コードに変換
 */
export function venueToPlaceCode(venue: string): string {
  const venueMap: { [key: string]: string } = {
    '札幌': '01',
    '函館': '02',
    '福島': '03',
    '新潟': '04',
    '東京': '05',
    '中山': '06',
    '中京': '07',
    '京都': '08',
    '阪神': '09',
    '小倉': '10'
  }
  const placeCode = venueMap[venue]
  if (!placeCode) throw new Error(`Unknown venue: ${venue}. Valid venues are: ${Object.keys(venueMap).join(', ')}`)
  return placeCode
}

/**
 * 日目をJRDB形式に変換（1, 2, 3, ... → 1, 2, 3, ... / a, b, c, ... → a, b, c, ...）
 */
export function dayToJRDBFormat(day: string | number | null | undefined): string {
  if (day == null) throw new Error('day is required but was null or undefined')
  
  // 数値の場合はそのまま文字列に変換
  if (typeof day === 'number') {
    return day.toString()
  }
  
  // 文字列の場合は小文字に変換（a, b, cなど）
  return day.toString().toLowerCase()
}

/**
 * 開催回数をJRDB形式に変換（1桁の文字列）
 */
export function roundToJRDBFormat(round: number | null | undefined): string {
  if (round == null) throw new Error('round is required but was null or undefined')
  
  return round.toString() // 1桁のまま
}

/**
 * レース番号をJRDB形式に変換（2桁の文字列）
 */
export function raceNumberToJRDBFormat(raceNumber: number | string | null | undefined): string {
  if (raceNumber == null) throw new Error('raceNumber is required but was null or undefined')
  
  const num = typeof raceNumber === 'string' ? parseInt(raceNumber) : raceNumber
  if (isNaN(num) || num <= 0) throw new Error(`Invalid raceNumber: ${raceNumber}. Must be a positive number.`)
  return num.toString().padStart(2, '0')
}

/**
 * 年をJRDB形式に変換（2桁の文字列）
 */
export function yearToJRDBFormat(year: number | null | undefined): string {
  if (year == null) throw new Error('year is required but was null or undefined')
  // 年の下2桁を取得
  return String(year % 100).padStart(2, '0')
}

/**
 * Raceオブジェクトからrace_id（JRDB原典キー）を生成（JRDB仕様に準拠）
 * 形式: 場コード_回_日目_R
 */
export function generateRaceKey(race: {
  raceDate?: Date | any
  date?: Date | any  // 後方互換性のため
  racecourse: string
  raceNumber: number
  round?: number | null
  day?: string | number | null  // 開催日目（必須）
}): string {
  // 場コード
  const placeCode = venueToPlaceCode(race.racecourse)
  
  // 開催回数（必須）
  const round = roundToJRDBFormat(race.round)
  
  // 日目（必須）
  const dayStr = dayToJRDBFormat(race.day)
  
  // レース番号（2桁）
  const raceNumber = raceNumberToJRDBFormat(race.raceNumber)
  
  // race_idを生成: 場コード_回_日目_R（JRDB仕様に準拠）
  return `${placeCode}_${round}_${dayStr}_${raceNumber}`
}

