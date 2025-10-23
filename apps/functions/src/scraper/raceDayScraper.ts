import { logger } from 'firebase-functions'
import type { JRARaceData } from '../../../shared/jra'

/**
 * 1日のレースページからレース情報を取得
 */
export async function getRaceDayData(page: any, dayUrl: string) {
  try {
    // 相対URLを絶対URLに変換
    const fullUrl = dayUrl.startsWith('http') ? dayUrl : `https://www.jra.go.jp${dayUrl}`
    
    logger.info('Accessing race day page', { url: fullUrl })
    
    await page.goto(fullUrl, { waitUntil: 'networkidle' })
    
    // レース情報のテーブルを取得
    const raceData = await page.$$eval('table tr', (rows: any[]) => {
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
        const parsedRace = parseRaceInfo(race)
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
function parseRaceInfo(race: any): any {
  try {
    const { raceNumber, raceInfo, startTime } = race
    
    // レース名、距離、コース、グレードを抽出
    const gradeMatch = raceInfo.match(/(G[Ⅰ1]|G[Ⅱ2]|G[Ⅲ3]|重賞|特別|新馬|未勝利|1勝クラス|2勝クラス|3勝クラス)/)
    const distanceMatch = raceInfo.match(/(\d{3,4})m/)
    const surfaceMatch = raceInfo.match(/(芝|ダート|障害)/)
    const ageMatch = raceInfo.match(/(\d)歳/)
    
    // 競馬場を推定（URLから）
    const venueMatch = raceInfo.match(/(東京|中山|阪神|京都|中京|新潟|小倉|福島|函館|札幌)/)
    
    return {
      raceName: gradeMatch ? gradeMatch[0] : '一般レース',
      racecourse: venueMatch ? venueMatch[0] : '未定',
      date: new Date(`2024-10-${raceNumber.padStart(2, '0')}`),
      grade: gradeMatch ? gradeMatch[0] : '一般',
      surface: surfaceMatch ? surfaceMatch[0] : '芝',
      distance: distanceMatch ? parseInt(distanceMatch[1]) : 1600,
      age: ageMatch ? parseInt(ageMatch[1]) : 3,
      startTime: startTime || '未定',
      prize: 0,
      description: raceInfo,
      source: 'JRA Race Day',
      scrapedAt: new Date()
    }
  } catch (error) {
    logger.error('Error parsing race info', { race, error })
    return null
  }
}
