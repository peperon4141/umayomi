import { onRequest } from 'firebase-functions/v2/https'
import { logger } from 'firebase-functions'
import { initializeApp } from 'firebase-admin/app'
import { fetchJRAHtmlWithPlaywright } from './utils/htmlFetcher'
import { parseJRACalendar } from './parser/jra/calendarParser'
import { parseJRARaceResult } from './parser/jra/raceResultParser'
import { saveRacesToFirestore } from './utils/firestoreSaver'
import { generateJRACalendarUrl, generateJRARaceResultUrl } from './utils/urlGenerator'

// Firebase Admin SDKを初期化
initializeApp()

/**
 * JRAデータを取得・保存するCloud Function
 * 年と月を引数で受け取る
 */
export const scrapeJRACalendar = onRequest(
  { timeoutSeconds: 300, memory: '1GiB' },
  async (request, response) => {
    logger.info('JRA scraping function called')

    try {
      const { year, month } = request.query

      if (!year || !month) {
        response.status(400).send({success: false, error: 'year and month parameters are required'})
        return
      }

      const targetYear = parseInt(year as string)
      const targetMonth = parseInt(month as string)
      
      const url = generateJRACalendarUrl(targetYear, targetMonth)
      const html = await fetchJRAHtmlWithPlaywright(url)
      const races = parseJRACalendar(html, targetYear, targetMonth)
      const savedCount = await saveRacesToFirestore(races)

      response.send({
        success: true,
        message: `${targetYear}年${targetMonth}月のJRAデータの取得・保存が完了しました`,
        racesCount: races.length,
        savedCount,
        url,
        year: targetYear,
        month: targetMonth
      })

    } catch (error) {
      logger.error('JRA scraping failed', { error })
      response.status(500).send({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }
)

/**
 * JRAカレンダーとレース結果データを一括取得・保存するCloud Function
 * 年と月を引数で受け取り、各日程のレース結果も含めて取得
 */
export const scrapeJRACalendarWithRaceResults = onRequest(
  { timeoutSeconds: 600, memory: '2GiB' },
  async (request, response) => {
    logger.info('JRA calendar with race results scraping function called')

    try {
      const { year, month } = request.query

      if (!year || !month) {
        response.status(400).send({
          success: false,
          error: 'year and month parameters are required'
        })
        return
      }

      const targetYear = parseInt(year as string)
      const targetMonth = parseInt(month as string)
      
      const calendarUrl = generateJRACalendarUrl(targetYear, targetMonth)
      
      // 1. カレンダーデータを取得
      const calendarHtml = await fetchJRAHtmlWithPlaywright(calendarUrl)
      const calendarRaces = parseJRACalendar(calendarHtml, targetYear, targetMonth)
      
      logger.info('Calendar races found', { count: calendarRaces.length })
      
      // 2. 各日程のレース結果データを取得
      const allRaceResults: any[] = []
      const processedDates = new Set<string>()
      
      for (const race of calendarRaces) {
        const raceDate = race.date
        const dateKey = raceDate.toISOString().split('T')[0] // YYYY-MM-DD形式
        
        // 同じ日付のレース結果は既に処理済みの場合はスキップ
        if (processedDates.has(dateKey)) {
          continue
        }
        
        processedDates.add(dateKey)
        
        try {
          const day = raceDate.getUTCDate()
          const raceResultUrl = generateJRARaceResultUrl(targetYear, targetMonth, day)
          const raceResultHtml = await fetchJRAHtmlWithPlaywright(raceResultUrl)
          const raceResults = parseJRARaceResult(raceResultHtml, targetYear, targetMonth, day)
          
          allRaceResults.push(...raceResults)
          logger.info('Race results fetched for date', { date: dateKey, count: raceResults.length })
        } catch (error) {
          logger.warn('Failed to fetch race results for date', { date: dateKey, error })
          // エラーが発生しても処理を続行
        }
      }
      
      // 3. すべてのデータをFirestoreに保存
      const allRaces = [...calendarRaces, ...allRaceResults]
      const savedCount = await saveRacesToFirestore(allRaces)

      response.send({
        success: true,
        message: `${targetYear}年${targetMonth}月のJRAカレンダーとレース結果データの取得・保存が完了しました`,
        calendarRacesCount: calendarRaces.length,
        raceResultsCount: allRaceResults.length,
        totalRacesCount: allRaces.length,
        savedCount,
        calendarUrl,
        processedDates: Array.from(processedDates),
        year: targetYear,
        month: targetMonth
      })

    } catch (error) {
      logger.error('JRA calendar with race results scraping failed', { error })
      response.status(500).send({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }
)

