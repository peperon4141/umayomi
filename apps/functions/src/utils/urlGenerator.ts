/**
 * JRAサイトのURLを生成するユーティリティ
 */

/**
 * JRAカレンダーページのURLを生成
 */
export function generateJRACalendarUrl(year: number, month: number): string {
  const monthNames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                     'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
  
  if (month < 1 || month > 12) {
    throw new Error(`Invalid month: ${month}. Must be between 1 and 12.`)
  }
  
  return `https://www.jra.go.jp/keiba/calendar${year}/${monthNames[month - 1]}.html`
}

/**
 * JRAレース結果ページのURLを生成
 */
export function generateJRARaceResultUrl(year: number, month: number, day: number): string {
  const monthStr = month.toString().padStart(2, '0')
  const dayStr = day.toString().padStart(2, '0')
  
  return `https://www.jra.go.jp/keiba/calendar${year}/${year}/${month}/${monthStr}${dayStr}.html`
}
