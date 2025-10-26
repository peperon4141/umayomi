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
          if (raceData) {
            races.push(raceData)
          }
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
    if (text) {
      elements.push($raceDiv)
    }
  })
  
  return elements
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

    return {
      raceNumber: index + 1,
      raceName,
      grade,
      venue,
      date,
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
    /\(GⅠ\)/, /\(GⅡ\)/, /\(GⅢ\)/, /\(G1\)/, /\(G2\)/, /\(G3\)/, /\(J・GⅡ\)/
  ]
  
  let raceName = text
  for (const pattern of gradePatterns) {
    raceName = raceName.replace(pattern, '').trim()
  }
  
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
  return null
}

/**
 * 親要素から競馬場を抽出
 */
function extractVenueFromParent($: cheerio.CheerioAPI, element: cheerio.Cheerio<any>): string | null {
  // レース要素の親のtd要素から競馬場を抽出
  const $td = element.closest('td')
  if ($td.length === 0) return null
  
  const tdText = $td.text()
  
  // レース名の前にある競馬場名を抽出
  const raceName = extractRaceName(element.text())
  if (!raceName) return null
  
  // 正規表現で競馬場名を抽出（レース名の直前）
  const venuePatterns = [
    new RegExp(`(東京|京都|新潟)${raceName}`),
    new RegExp(`(東京|京都|新潟)\\s*${raceName}`)
  ]
  
  for (const pattern of venuePatterns) {
    const match = tdText.match(pattern)
    if (match) {
      return match[1]
    }
  }
  
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

