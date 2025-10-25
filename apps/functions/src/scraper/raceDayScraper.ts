import { logger } from 'firebase-functions'

/**
 * 1日のレースページからレース情報を取得
 */
export async function getRaceDayData(page: any, dayUrl: string) {
  try {
    // 相対URLを絶対URLに変換
    const fullUrl = dayUrl.startsWith('http') ? dayUrl : `https://www.jra.go.jp${dayUrl}`
    
    logger.info('Accessing race day page', { url: fullUrl })
    
    await page.goto(fullUrl, { waitUntil: 'networkidle' })
    
    // ページのHTML構造をデバッグ用にログ出力
    const pageTitle = await page.title()
    const pageContent = await page.content()
    logger.info('Race day page loaded', { 
      title: pageTitle,
      contentLength: pageContent.length,
      url: fullUrl
    })
    
    // レース情報のテーブルを取得（複数のセレクターを試す）
    let raceData = []
    
    // セレクター1: 標準的なテーブル構造
    try {
      raceData = await page.$$eval('table tr', (rows: any[]) => {
        return rows.map((row: any) => {
          const cells = row.querySelectorAll('td, th')
          if (cells.length < 3) return null
          
          const raceNumber = cells[0]?.textContent?.trim()
          const raceInfo = cells[1]?.textContent?.trim()
          const startTime = cells[2]?.textContent?.trim()
          
          if (!raceNumber || !raceInfo) return null
          
          return {
            raceNumber,
            raceInfo,
            startTime,
            fullText: row.textContent?.trim() || ''
          }
        }).filter((item: any) => item && item.raceNumber && item.raceInfo)
      })
    } catch (error) {
      logger.warn('Standard table selector failed', { error })
    }
    
    // セレクター2: レース情報のdiv構造
    if (raceData.length === 0) {
      try {
        raceData = await page.$$eval('.race-info, .race', (elements: any[]) => {
          return elements.map((element: any) => {
            const raceNumber = element.querySelector('.race-number')?.textContent?.trim()
            const raceName = element.querySelector('.race-name')?.textContent?.trim()
            const startTime = element.querySelector('.start-time')?.textContent?.trim()
            
            if (!raceNumber || !raceName) return null
            
            return {
              raceNumber,
              raceInfo: raceName,
              startTime,
              fullText: element.textContent?.trim() || ''
            }
          }).filter((item: any) => item && item.raceNumber && item.raceInfo)
        })
      } catch (error) {
        logger.warn('Race info div selector failed', { error })
      }
    }
    
    // セレクター3: 一般的なレース情報のリンク
    if (raceData.length === 0) {
      try {
        raceData = await page.$$eval('a[href*="/race/"], a[href*="/result/"]', (links: any[]) => {
          return links.map((link: any) => {
            const href = link.getAttribute('href')
            const text = link.textContent?.trim()
            
            if (!href || !text) return null
            
            // レース番号を抽出
            const raceNumberMatch = text.match(/(\d+)R/)
            const raceNumber = raceNumberMatch ? raceNumberMatch[1] : '1'
            
            return {
              raceNumber,
              raceInfo: text,
              startTime: '未定',
              fullText: text
            }
          }).filter((item: any) => item && item.raceNumber && item.raceInfo)
        })
      } catch (error) {
        logger.warn('Race link selector failed', { error })
      }
    }
    
    logger.info('Found race data', { 
      dayUrl: fullUrl,
      raceCount: raceData.length,
      races: raceData.map((race: any) => ({
        raceNumber: race.raceNumber,
        raceInfo: race.raceInfo,
        startTime: race.startTime
      }))
    })
    
    // レース情報を解析
    const races = []
    for (const race of raceData) {
      try {
        const parsedRace = parseRaceInfo(race, fullUrl)
        if (parsedRace) {
          races.push(parsedRace)
        }
      } catch (error) {
        logger.error('Error parsing race info', { race, error })
      }
    }
    
    logger.info('Parsed races', { 
      dayUrl: fullUrl,
      parsedCount: races.length
    })
    
    return races

  } catch (error) {
    logger.error('Error scraping race day', { dayUrl, error })
    return []
  }
}

/**
 * レース情報を解析
 */
function parseRaceInfo(race: any, dayUrl?: string): any {
  try {
    const { raceNumber, raceInfo, startTime } = race
    
    // レース名、距離、コース、グレードを抽出
    const gradeMatch = raceInfo.match(/(G[Ⅰ1]|G[Ⅱ2]|G[Ⅲ3]|重賞|特別|新馬|未勝利|1勝クラス|2勝クラス|3勝クラス)/)
    const distanceMatch = raceInfo.match(/(\d{3,4})m/)
    const surfaceMatch = raceInfo.match(/(芝|ダート|障害)/)
    
    // 競馬場を推定（レース情報とURLから）
    let venue = '未定'
    
    // レース情報から競馬場を抽出
    const venueMatch = raceInfo.match(/(東京|中山|阪神|京都|中京|新潟|小倉|福島|函館|札幌)/)
    if (venueMatch) {
      venue = venueMatch[0]
    } else if (dayUrl) {
      // URLから競馬場を推定
      const urlVenueMatch = dayUrl.match(/(東京|中山|阪神|京都|中京|新潟|小倉|福島|函館|札幌)/)
      if (urlVenueMatch) {
        venue = urlVenueMatch[0]
      }
    }
    
    // URLから日付を抽出
    let raceDate = new Date()
    if (dayUrl) {
      logger.info('Extracting date from URL', { dayUrl })
      
      // 複数の日付パターンを試す（より具体的なパターンを先に）
      const datePatterns = [
        /\/keiba\/calendar2025\/2025\/10\/(\d{4})/, // /keiba/calendar2025/2025/10/1004
        /\/keiba\/calendar2024\/2024\/10\/(\d{4})/, // /keiba/calendar2024/2024/10/1004
        /(\d{4})\/(\d{2})\/(\d{2})/,  // 2025/10/04
        /(\d{4})(\d{2})(\d{2})/,     // 20251004
        /(\d{4})-(\d{2})-(\d{2})/    // 2025-10-04
      ]
      
      for (const pattern of datePatterns) {
        const dateMatch = dayUrl.match(pattern)
        if (dateMatch) {
          logger.info('Pattern matched', { pattern: pattern.source, dateMatch })
          if (pattern.source.includes('calendar2025')) {
            // /keiba/calendar2025/2025/10/1004 パターン
            const dateStr = dateMatch[1] // "1004"
            const month = parseInt(dateStr.substring(0, 2)) // "10"
            const day = parseInt(dateStr.substring(2, 4)) // "04"
            raceDate = new Date(2025, month - 1, day) // 月は0-indexedなので-1
            logger.info('Date calculation', { dateStr, month, day, raceDate: raceDate.toISOString() })
            logger.info('Date extracted from calendar2025 URL', { dayUrl, raceDate: raceDate.toISOString() })
          } else if (pattern.source.includes('calendar2024')) {
            // /keiba/calendar2024/2024/10/1004 パターン
            const dateStr = dateMatch[1] // "1004"
            const month = parseInt(dateStr.substring(0, 2)) // "10"
            const day = parseInt(dateStr.substring(2, 4)) // "04"
            raceDate = new Date(2024, month - 1, day) // 月は0-indexedなので-1
            logger.info('Date extracted from calendar2024 URL', { dayUrl, raceDate: raceDate.toISOString() })
          } else {
            // 通常の日付パターン
            const [, year, month, day] = dateMatch
            raceDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))
            logger.info('Date extracted from standard URL', { dayUrl, raceDate: raceDate.toISOString() })
          }
          break
        }
      }
      
      // 日付が抽出できなかった場合は現在の日付を使用
      if (raceDate.getTime() === new Date().getTime()) {
        logger.warn('Could not extract date from URL, using current date', { dayUrl })
      }
    }
    
    // レース番号を数値に変換
    const raceNumberNum = parseInt(raceNumber.replace(/[^\d]/g, '')) || 1
    
    return {
      raceNumber: raceNumberNum,
      raceName: gradeMatch ? gradeMatch[0] : '一般レース',
      grade: gradeMatch ? gradeMatch[0] : '一般',
      distance: distanceMatch ? parseInt(distanceMatch[1]) : 1600,
      surface: surfaceMatch ? surfaceMatch[0] : '芝',
      weather: '晴れ', // デフォルト値
      trackCondition: '良', // デフォルト値
      startTime: startTime || '未定',
      description: raceInfo,
      venue: venue,
      date: raceDate,
      prize: 0,
      scrapedAt: new Date()
    }
  } catch (error) {
    logger.error('Error parsing race info', { race, error })
    return null
  }
}
