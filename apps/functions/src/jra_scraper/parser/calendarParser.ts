import { logger } from 'firebase-functions'
import * as cheerio from 'cheerio'

/**
 * JRAカレンダーページのHTMLをパースしてレースデータを抽出
 */
export function parseJRACalendar(html: string, year: number, month: number): any[] {
  const races: any[] = []
  
  try {
    logger.info('Starting JRA calendar HTML parsing', { htmlLength: html.length })
    
    const $ = cheerio.load(html)
    const raceElements = extractRaceElements($)
    
    if (raceElements.length > 0) {
      logger.info('Found race elements', { count: raceElements.length })
      
      raceElements.forEach((element, index) => {
        try {
          const raceData = parseRaceElement($, element, index, year, month)
          if (raceData) races.push(raceData)
          
        } catch (error) {
          logger.warn('Failed to parse race element', { index, error })
        }
      })
    } else {
      logger.warn('No race elements found in HTML')
      throw new Error('No race elements found in HTML')
    }
    
    logger.info('JRA calendar parsed successfully', { 
      racesCount: races.length,
      htmlLength: html.length 
    })
    
  } catch (error) {
    logger.error('Failed to parse JRA calendar', { error })
    throw error
  }
  
  return races
}

/**
 * HTMLからレース要素を抽出
 */
export function extractRaceElements($: cheerio.CheerioAPI): cheerio.Cheerio<any>[] {
  const elements: cheerio.Cheerio<any>[] = []
  
  // レース情報を含むdiv要素を抽出（空でないもののみ）
  $('.race').each((_, raceDiv) => {
    const $raceDiv = $(raceDiv)
    const text = $raceDiv.text().trim()
    
    // 空でない要素のみを抽出
    if (text) elements.push($raceDiv)
    
  })
  
  return elements
}

/**
 * HTMLから開催日を抽出（カレンダーページの開催日をすべて取得）
 */
export function extractRaceDates($: cheerio.CheerioAPI, year: number, month: number): Date[] {
  const dates: Date[] = []
  const processedDates = new Set<string>()
  
  // 開催日を示す.kaisaiクラスを持つtd要素から日付を抽出
  $('.rc_table .kaisai').each((_, elem) => {
    const $td = $(elem).closest('td')
    const classNames = $td.attr('class') || ''
    const dayMatch = classNames.match(/rc-day(\d+)/)
    
    if (dayMatch) {
      const day = parseInt(dayMatch[1])
      const date = new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0))
      const dateKey = date.toISOString().split('T')[0]
      
      // 重複を避ける
      if (!processedDates.has(dateKey)) {
        processedDates.add(dateKey)
        dates.push(date)
      }
    }
  })
  
  return dates.sort((a, b) => a.getTime() - b.getTime())
}

/**
 * レース要素からデータを抽出
 */
export function parseRaceElement($: cheerio.CheerioAPI, element: cheerio.Cheerio<any>, index: number, year: number, month: number): any | null {
  if (!element) return null
  
  try {
    const text = element.text()
    
    const raceName = extractRaceName(text)
    if (!raceName) return null

    const grade = extractGrade(text)
    if (!grade) return null

    const venue = extractVenueFromParent($, element)
    if (!venue) return null

    const date = extractDateFromParent($, element, year, month)
    if (!date) return null

    // カレンダーページから開催回数と日目を抽出（可能な場合）
    const roundAndDay = extractRoundAndDayFromCalendar($, element)
    
    return {
      raceNumber: index + 1,
      raceName,
      grade,
      venue,
      date,
      year,
      month,
      round: roundAndDay.round,
      day: roundAndDay.day,
      // カレンダーページには距離データがないため、デフォルト値を設定
      distance: null,
      surface: null,
      weather: null,
      trackCondition: null,
      scrapedAt: new Date(Date.UTC(new Date().getFullYear(), new Date().getMonth(), new Date().getDate(), 0, 0, 0, 0))
    }
  } catch (error) {
    logger.warn('Failed to parse race element', { error })
    return null
  }
}

/**
 * レース名を抽出
 */
function extractRaceName(text: string): string | null {
  // グレード情報を除去してレース名を抽出
  const gradePatterns = [
    /\(GⅠ\)/, /\(GⅡ\)/, /\(GⅢ\)/, /\(G1\)/, /\(G2\)/, /\(G3\)/, /\(J・GⅡ\)/, /\(J・GⅢ\)/
  ]
  
  let raceName = text
  for (const pattern of gradePatterns) 
    raceName = raceName.replace(pattern, '').trim()
  
  
  // 空でない場合はレース名として返す
  return raceName || null
}

/**
 * グレードを抽出
 */
function extractGrade(text: string): string | null {
  if (text.includes('GⅠ') || text.includes('G1')) return 'GⅠ'
  if (text.includes('GⅡ') || text.includes('G2')) return 'GⅡ'
  if (text.includes('GⅢ') || text.includes('G3')) return 'GⅢ'
  if (text.includes('J・GⅡ')) return 'J・GⅡ'
  if (text.includes('J・GⅢ')) return 'GⅢ'
  return null
}

/**
 * 親要素から競馬場を抽出
 */
function extractVenueFromParent($: cheerio.CheerioAPI, element: cheerio.Cheerio<any>): string | null {
  // レース要素の親のk_line要素から競馬場を抽出
  const $kline = element.closest('.k_line')
  if ($kline.length === 0) return null
  
  // k_line要素内の.rc要素から競馬場名を抽出
  const venue = $kline.find('.rc').text().trim()
  
  if (!venue) return null
  
  // JRAの競馬場名をそのまま返す
  const validVenues = ['東京', '京都', '新潟', '中山', '阪神', '札幌', '函館', '福島', '中京', '小倉']
  if (validVenues.includes(venue)) return venue
  
  
  return null
}

/**
 * 親要素から日付を抽出
 */
function extractDateFromParent($: cheerio.CheerioAPI, element: cheerio.Cheerio<any>, year: number, month: number): Date | null {
  // レース要素の親のtd要素から日付を抽出
  const $td = element.closest('td')
  if ($td.length === 0) return null
  
  // td要素のクラス名から日付を抽出（例：rc-day5）
  const classNames = $td.attr('class') || ''
  const dayMatch = classNames.match(/rc-day(\d+)/)
  
  if (dayMatch) {
    const day = parseInt(dayMatch[1])
    return new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0))
  }
  
  return null
}

/**
 * カレンダーページから開催回数と日目を抽出（可能な場合）
 */
function extractRoundAndDayFromCalendar($: cheerio.CheerioAPI, element: cheerio.Cheerio<any>): { round: number | null, day: string | null } {
  // カレンダーページ全体から開催回数と日目を抽出
  const pageText = $('body').text()
  
  // 「第○回」のパターンを検索
  const roundMatch = pageText.match(/第(\d+)回/)
  const round = roundMatch ? parseInt(roundMatch[1]) : null
  
  // 「○日目」のパターンを検索（1日目、2日目、...、a日目、b日目など）
  const dayMatch = pageText.match(/(\d+|[a-z])日目/)
  let day: string | null = null
  if (dayMatch) {
    day = dayMatch[1].toLowerCase()
  }
  
  return { round, day }
}

