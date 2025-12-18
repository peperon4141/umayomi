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
          
        } catch (error: any) {
          // roundがnullの場合のエラーは、fallbackを禁止するため、再スローする
          const errorMessage = error?.message || String(error) || ''
          if (errorMessage.includes('Failed to extract round from JRA calendar page')) {
            logger.error('Failed to extract round from calendar page', { index, error, errorMessage })
            throw error
          }
          logger.warn('Failed to parse race element', { index, error, errorMessage })
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

    // カレンダーページから開催回数を抽出（オプション）
    // 注意: カレンダーページには開催回数の情報が含まれていない場合があるため、
    // レース結果ページから取得したデータで上書きされる可能性がある
    const round = extractRoundFromCalendar($)
    
    // roundがnullの場合でもエラーを投げない（レース結果ページから取得したデータで上書きされる）
    // ただし、ログには記録する
    if (round == null) 
      logger.warn('Failed to extract round from JRA calendar page. Will be updated from race result page.', {
        raceName,
        venue,
        date: date.toISOString().split('T')[0]
      })
    
    
    return {
      raceNumber: index + 1,
      raceName,
      grade,
      venue,
      raceDate: date,
      year,
      month,
      round: round, // nullの可能性がある（レース結果ページから取得したデータで上書きされる）
      // カレンダーページには距離データがないため、デフォルト値を設定
      distance: null,
      surface: null,
      weather: null,
      trackCondition: null,
      scrapedAt: new Date(Date.UTC(new Date().getFullYear(), new Date().getMonth(), new Date().getDate(), 0, 0, 0, 0))
    }
  } catch (error: any) {
    // roundがnullの場合のエラーは、fallbackを禁止するため、再スローする
    const errorMessage = error?.message || String(error) || ''
    if (errorMessage.includes('Failed to extract round from JRA calendar page')) {
      logger.error('Failed to extract round from calendar page in parseRaceElement', { error, errorMessage })
      throw error
    }
    logger.warn('Failed to parse race element', { error, errorMessage })
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
 * カレンダーページから開催回数を抽出（可能な場合）
 */
function extractRoundFromCalendar($: cheerio.CheerioAPI): number | null {
  // カレンダーページ全体から開催回数を抽出
  // より具体的なセレクタを使用
  let pageText = ''
  const foundRounds: number[] = []
  
  // 1. ページタイトルから抽出を試みる
  const pageTitle = $('title').text()
  if (pageTitle) {
    pageText += pageTitle + ' '
    const titleRoundMatch = pageTitle.match(/第(\d+)回/)
    if (titleRoundMatch) foundRounds.push(parseInt(titleRoundMatch[1]))
  }
  
  // 2. ヘッダー部分を優先的に検索
  const headerSelectors = [
    'h1', 'h2', 'h3',
    '.header', '.title', '.page-title',
    '.month_title', '.kaisai_title',
    '.rc_table_header', '.calendar_header',
    '.main_title', '.sub_title',
    '#main_title', '#sub_title'
  ]
  
  for (const selector of headerSelectors) {
    const headerText = $(selector).text()
    if (headerText) {
      pageText += headerText + ' '
      const roundMatch = headerText.match(/第(\d+)回/)
      if (roundMatch) {
        const round = parseInt(roundMatch[1])
        if (!foundRounds.includes(round)) foundRounds.push(round)
      }
    }
  }
  
  // 3. レース要素内から開催回数を抽出（レース名や競馬場情報に含まれる場合がある）
  $('.race, .k_line, .rc').each((_, elem) => {
    const elemText = $(elem).text()
    const roundMatch = elemText.match(/第(\d+)回/)
    if (roundMatch) {
      const round = parseInt(roundMatch[1])
      if (!foundRounds.includes(round)) foundRounds.push(round)
    }
  })
  
  // 4. メインコンテンツエリアから抽出を試みる
  const mainContentSelectors = [
    '.main_content', '#main_content',
    '.calendar_content', '#calendar_content',
    '.rc_table', '#rc_table',
    '#contentsBody', '.contents_body'
  ]
  
  for (const selector of mainContentSelectors) {
    const contentText = $(selector).first().text()
    if (contentText) {
      pageText += contentText.substring(0, 2000) + ' '
      const roundMatch = contentText.match(/第(\d+)回/)
      if (roundMatch) {
        const round = parseInt(roundMatch[1])
        if (!foundRounds.includes(round)) foundRounds.push(round)
      }
    }
  }
  
  // 5. ヘッダーから取得できなかった場合はbody全体から検索（最初の5000文字）
  if (!pageText || pageText.trim().length < 10) {
    const bodyText = $('body').text()
    pageText = bodyText.substring(0, 5000) // 最初の5000文字
  }
  
  // 6. ページ全体から「第○回」のパターンを検索
  const roundPatterns = [
    /第(\d+)回/,           // 第○回
    /(\d+)回目/,           // ○回目
    /回数[：:]\s*(\d+)/,   // 回数：○
    /回[：:]\s*(\d+)/      // 回：○
  ]
  
  // まず、見つかった開催回数を使用（最も頻繁に出現するものを採用）
  if (foundRounds.length > 0) {
    // 最も頻繁に出現する回数を採用
    const roundCounts: { [key: number]: number } = {}
    foundRounds.forEach(r => {
      roundCounts[r] = (roundCounts[r] || 0) + 1
    })
    const mostFrequentRound = Object.keys(roundCounts).reduce((a, b) => 
      roundCounts[parseInt(a)] > roundCounts[parseInt(b)] ? a : b
    )
    const round = parseInt(mostFrequentRound)
    logger.info('Round extracted from calendar page', { round, allRounds: foundRounds, pageTextSample: pageText.substring(0, 500) })
    return round
  }
  
  // 見つからなかった場合は、ページ全体から検索
  let round: number | null = null
  for (const pattern of roundPatterns) {
    const roundMatch = pageText.match(pattern)
    if (roundMatch) {
      round = parseInt(roundMatch[1])
      break
    }
  }
  
  logger.info('Extracted round from calendar', { 
    round, 
    pageTextSample: pageText.substring(0, 500),
    foundRounds,
    extractedFrom: round && foundRounds.includes(round) ? 'found rounds' : (pageText.length > 0 ? 'page content' : 'empty')
  })
  
  return round
}

