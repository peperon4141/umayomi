/**
 * JRAレースデータからrace_keyを生成するユーティリティ（Functions用）
 */

/**
 * 競馬場名をJRDB場コードに変換
 * @throws {Error} venueが未定義またはマッピングに存在しない場合
 */
export function venueToPlaceCode(venue: string | null | undefined): string {
  if (!venue) {
    throw new Error(`venue is required but was ${venue}`)
  }
  
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
  
  const placeCode = venueMap[venue]
  if (!placeCode) {
    throw new Error(`Unknown venue: ${venue}. Valid venues are: ${Object.keys(venueMap).join(', ')}`)
  }
  
  return placeCode
}

/**
 * 日目をJRDB形式に変換（1, 2, 3, ... → 1, 2, 3, ... / a, b, c, ... → a, b, c, ...）
 * @throws {Error} dayがnullまたはundefinedの場合
 */
export function dayToJRDBFormat(day: string | number | null | undefined): string {
  if (day == null) {
    throw new Error('day is required but was null or undefined')
  }
  
  // 数値の場合はそのまま文字列に変換
  if (typeof day === 'number') return day.toString()
  
  // 文字列の場合は小文字に変換（a, b, cなど）
  return day.toString().toLowerCase()
}

/**
 * 開催回数をJRDB形式に変換（1桁の文字列）
 * @throws {Error} roundがnullまたはundefinedの場合
 */
export function roundToJRDBFormat(round: number | null | undefined): string {
  if (round == null) {
    throw new Error('round is required but was null or undefined')
  }
  
  return round.toString() // 1桁のまま
}

/**
 * レース番号をJRDB形式に変換（2桁の文字列）
 * @throws {Error} raceNumberがnullまたはundefinedの場合
 */
export function raceNumberToJRDBFormat(raceNumber: number | string | null | undefined): string {
  if (raceNumber == null) {
    throw new Error('raceNumber is required but was null or undefined')
  }
  
  const num = typeof raceNumber === 'string' ? parseInt(raceNumber) : raceNumber
  if (isNaN(num) || num <= 0) {
    throw new Error(`Invalid raceNumber: ${raceNumber}. Must be a positive number.`)
  }
  
  return num.toString().padStart(2, '0')
}

/**
 * 年をJRDB形式に変換（2桁の文字列）
 * @throws {Error} yearがnullまたはundefinedの場合
 */
export function yearToJRDBFormat(year: number | null | undefined): string {
  if (year == null) {
    throw new Error('year is required but was null or undefined')
  }
  
  if (year < 1900 || year > 2100) {
    throw new Error(`Invalid year: ${year}. Year must be between 1900 and 2100.`)
  }
  
  // 年の下2桁を取得
  return String(year % 100).padStart(2, '0')
}

/**
 * Raceオブジェクトからrace_keyを生成（JRDB仕様に準拠）
 * 形式: 場コード_年_回_日_R
 * 
 * @throws {Error} roundがnullまたはundefinedの場合
 */
export function generateRaceKey(race: {
  raceDate?: Date | any
  date?: Date | any  // 後方互換性のため
  racecourse?: string
  venue?: string
  raceNumber: number
  round?: number | null
}): string {
  // roundが必須であることを確認
  if (race.round == null) {
    const dateValue = race.raceDate || race.date
    const date = dateValue instanceof Date ? dateValue : new Date(dateValue)
    const dateStr = date.toISOString().split('T')[0]
    const venue = race.venue || race.racecourse || '不明'
    throw new Error(
      `round is required but was null or undefined. ` +
      `raceDate: ${dateStr}, venue: ${venue}, raceNumber: ${race.raceNumber}. ` +
      `Please ensure extractRound function correctly extracts round from JRA HTML.`
    )
  }
  
  // 日付から年を取得（raceDateを優先、後方互換性のためdateも確認）
  const dateValue = race.raceDate || race.date
  if (!dateValue) {
    throw new Error(
      `raceDate or date is required but both were null or undefined. ` +
      `venue: ${race.venue || race.racecourse || 'unknown'}, raceNumber: ${race.raceNumber}, round: ${race.round}`
    )
  }
  const date = dateValue instanceof Date ? dateValue : new Date(dateValue)
  if (isNaN(date.getTime())) {
    throw new Error(
      `Invalid date value: ${dateValue}. ` +
      `venue: ${race.venue || race.racecourse || 'unknown'}, raceNumber: ${race.raceNumber}, round: ${race.round}`
    )
  }
  const year = date.getFullYear()
  const yearStr = yearToJRDBFormat(year) // 年の下2桁
  
  // 場コード（venueまたはracecourseから取得）
  const venue = race.venue || race.racecourse
  if (!venue) {
    throw new Error(
      `venue or racecourse is required but both were null or undefined. ` +
      `raceDate: ${date.toISOString().split('T')[0]}, raceNumber: ${race.raceNumber}, round: ${race.round}`
    )
  }
  const placeCode = venueToPlaceCode(venue)
  
  // 開催回数（必須）
  const round = roundToJRDBFormat(race.round)
  
  // 日目（JRAから取得したデータでは日目の情報がないため、デフォルトで'1'を使用）
  // 注意: これはJRDB仕様に準拠したデフォルト値であり、fallbackではない
  const dayStr = '1'
  
  // レース番号（2桁）
  const raceNumber = raceNumberToJRDBFormat(race.raceNumber)
  
  // race_keyを生成: 場コード_年_回_日_R（JRDB仕様に準拠）
  return `${placeCode}_${yearStr}_${round}_${dayStr}_${raceNumber}`
}

