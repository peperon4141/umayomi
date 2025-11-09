/**
 * 日付フォーマットユーティリティ
 */

/**
 * 年、月、日からDateオブジェクトを作成
 */
export function createDateFromYMD(year: number, month: number, day: number): Date {
  return new Date(year, month - 1, day)
}

/**
 * 年、月、日からISO形式の日付文字列を作成（YYYY-MM-DD）
 */
export function formatDateISO(year: number, month: number, day: number): string {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

/**
 * 年、月、日からJRDB形式の日付文字列を作成（YYMMDD）
 */
export function formatDateJRDB(year: number, month: number, day: number): string {
  const year2Digit = String(year).slice(-2)
  return `${year2Digit}${String(month).padStart(2, '0')}${String(day).padStart(2, '0')}`
}

/**
 * 年から2桁の年文字列を作成（YY）
 */
export function formatYear2Digit(year: number): string {
  return String(year).slice(-2)
}

