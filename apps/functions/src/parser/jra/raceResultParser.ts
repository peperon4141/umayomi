import { logger } from 'firebase-functions'
import * as cheerio from 'cheerio'

/**
 * JRAレース結果ページのHTMLをパースしてレース結果データを抽出
 */
export function parseJRARaceResult(html: string, year: number, month: number, day: number): any[] {
  const races: any[] = []

  try {
    logger.info('Starting JRA race result HTML parsing', { htmlLength: html.length })

    const $ = cheerio.load(html)
    const raceInfo = extractRaceInfo($)

    if (raceInfo.length > 0) {
      logger.info('Found race info', { count: raceInfo.length })

      raceInfo.forEach((race: any, index: number) => {
        try {
          const raceData = {
            raceNumber: race.raceNumber,
            raceName: race.raceName,
            venue: race.venue,
            date: new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0)),
            distance: race.distance,
            surface: race.surface,
            startTime: parseStartTime(year, month, day, race.startTime),
            scrapedAt: new Date(Date.UTC(new Date().getFullYear(), new Date().getMonth(), new Date().getDate(), 0, 0, 0, 0))
          }
          races.push(raceData)
        } catch (error) {
          logger.warn('Failed to parse race info', { index, error })
        }
      })
    } else {
      logger.warn('No race info found in HTML')
      throw new Error('No race info found in HTML')
    }

    logger.info('JRA race result parsed successfully', {
      racesCount: races.length,
      htmlLength: html.length
    })

  } catch (error) {
    logger.error('Failed to parse JRA race result', { error })
    throw error
  }

  return races
}

/**
 * レース基本情報を抽出
 */
export function extractRaceInfo($: cheerio.CheerioAPI): any[] {
  const races: any[] = []

  // 東京競馬場のレース情報を抽出
  $('#rcA tbody tr').each((_, element) => {
    const $row = $(element)
    const raceNumber = parseInt($row.find('th.num').text().replace('レース', '').trim())
    const stakesName = $row.find('td.name p.stakes strong').text().trim().replace(/\s+/g, ' ') || 
                      $row.find('td.name p.stakes a strong').text().trim().replace(/\s+/g, ' ')
    const raceClassName = $row.find('td.name p.race_class').text().trim()
    const raceName = stakesName || raceClassName
    const distance = parseInt($row.find('td.name p.race_cond span.dist').text().replace(',', ''))
    const surface = $row.find('td.name p.race_cond span.type').text().includes('芝') ? '芝' : 'ダ'
    const startTime = $row.find('td.time').text().trim()

    if (raceNumber && raceName && distance && startTime) {
      races.push({
        raceNumber,
        raceName,
        venue: '東京',
        distance,
        surface,
        startTime
      })
    }
  })

  // 京都競馬場のレース情報を抽出
  $('#rcB tbody tr').each((_, element) => {
    const $row = $(element)
    const raceNumber = parseInt($row.find('th.num').text().replace('レース', '').trim())
    const stakesName = $row.find('td.name p.stakes strong').text().trim().replace(/\s+/g, ' ') || 
                      $row.find('td.name p.stakes a strong').text().trim().replace(/\s+/g, ' ')
    const raceClassName = $row.find('td.name p.race_class').text().trim()
    const raceName = stakesName || raceClassName
    const distance = parseInt($row.find('td.name p.race_cond span.dist').text().replace(',', ''))
    const surface = $row.find('td.name p.race_cond span.type').text().includes('芝') ? '芝' : 'ダ'
    const startTime = $row.find('td.time').text().trim()

    if (raceNumber && raceName && distance && startTime) {
      races.push({
        raceNumber,
        raceName,
        venue: '京都',
        distance,
        surface,
        startTime
      })
    }
  })

  return races
}

/**
 * 発走時刻をDate型に変換（JSTからUTCに変換）
 */
function parseStartTime(year: number, month: number, day: number, timeStr: string): Date {
  // "9時50分" 形式を解析
  const timeMatch = timeStr.match(/(\d+)時(\d+)分/)
  if (!timeMatch) {
    throw new Error(`Invalid time format: ${timeStr}`)
  }
  
  const hour = parseInt(timeMatch[1])
  const minute = parseInt(timeMatch[2])
  
  // JST時刻をUTCに変換（JST = UTC + 9時間）
  const utcHour = hour - 9
  const utcDate = new Date(Date.UTC(year, month - 1, day, utcHour, minute, 0, 0))
  
  // 日付が変わる場合の処理
  if (utcHour < 0) {
    utcDate.setUTCDate(utcDate.getUTCDate() - 1)
    utcDate.setUTCHours(utcHour + 24)
  }
  
  return utcDate
}


