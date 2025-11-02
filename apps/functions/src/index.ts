import { onRequest } from 'firebase-functions/v2/https'
import { logger } from 'firebase-functions'
import { initializeApp } from 'firebase-admin/app'
import { fetchJRAHtmlWithPlaywright } from './utils/htmlFetcher'
import { parseJRACalendar, extractRaceDates } from './parser/jra/calendarParser'
import * as cheerio from 'cheerio'
import { parseJRARaceResult } from './parser/jra/raceResultParser'
import { saveRacesToFirestore } from './utils/firestoreSaver'
import { generateJRACalendarUrl, generateJRARaceResultUrl } from './utils/urlGenerator'
import { saveFunctionLog, createSuccessLog, createErrorLog } from './utils/functionLogSaver'

// Firestore Emulatorに接続（開発環境の場合）
const isDevelopment = process.env.NODE_ENV === 'development' || 
                     process.env.FUNCTIONS_EMULATOR === 'true' ||
                     process.env.MODE === 'development'

if (isDevelopment) {
  // Firebase Admin SDKの環境変数を設定（initializeAppより前に設定）
  process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
  logger.info('Firestore Emulator環境変数を設定しました')
}

// Firebase Admin SDKを初期化
initializeApp()

/**
 * JRAデータを取得・保存するCloud Function
 * 年と月を引数で受け取る
 */
export const scrapeJRACalendar = onRequest(
  { timeoutSeconds: 300, memory: '1GiB', region: 'asia-northeast1' },
  async (request, response) => {
    const startTime = Date.now()
    logger.info('JRA scraping function called')

    try {
      const year = request.query.year || request.body.year
      const month = request.query.month || request.body.month
      
      logger.info('Received parameters', { 
        body: request.body, 
        query: request.query, 
        year, 
        month,
        yearType: typeof year,
        monthType: typeof month
      })

      if (!year || !month) {
        const errorMessage = 'year and month parameters are required'
        
        await saveFunctionLog(createErrorLog(
          'scrapeJRACalendar',
          year as string,
          month as string,
          errorMessage
        ))
        response.status(400).send({success: false, error: errorMessage})
        return
      }

      const targetYear = parseInt(year as string)
      const targetMonth = parseInt(month as string)
      
      const url = generateJRACalendarUrl(targetYear, targetMonth)
      const html = await fetchJRAHtmlWithPlaywright(url)
      const races = parseJRACalendar(html, targetYear, targetMonth)
      const savedCount = await saveRacesToFirestore(races)

      const executionTimeMs = Date.now() - startTime
      const message = `${targetYear}年${targetMonth}月のJRAデータの取得・保存が完了しました`
      
      // 成功時のログを保存
      await saveFunctionLog(createSuccessLog(
        'scrapeJRACalendar',
        year as string,
        month as string,
        message,
        {
          racesCount: races.length,
          savedCount,
          url,
          executionTimeMs
        }
      ))

      response.send({
        success: true,
        message,
        racesCount: races.length,
        savedCount,
        url,
        year: targetYear,
        month: targetMonth,
        executionTimeMs
      })

    } catch (error) {
      const executionTimeMs = Date.now() - startTime
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      logger.error('JRA scraping failed', { error })
      
      // エラー時のログを保存
      const errorYear = (request.body || request.query).year as string
      const errorMonth = (request.body || request.query).month as string
      
      await saveFunctionLog(createErrorLog(
        'scrapeJRACalendar',
        errorYear,
        errorMonth,
        errorMessage,
        { executionTimeMs }
      ))
      
      response.status(500).send({
        success: false,
        error: errorMessage,
        executionTimeMs
      })
    }
  }
)

/**
 * JRAレース結果データを取得・保存するCloud Function
 * 年、月、日を引数で受け取る
 */
export const scrapeJRARaceResult = onRequest(
  { timeoutSeconds: 300, memory: '1GiB', region: 'asia-northeast1' },
  async (request, response) => {
    const startTime = Date.now()
    logger.info('JRA race result scraping function called')

    try {
      const year = request.query.year || request.body.year
      const month = request.query.month || request.body.month
      const day = request.query.day || request.body.day

      if (!year || !month || !day) {
        const errorMessage = 'year, month, and day parameters are required'
        
        await saveFunctionLog(createErrorLog(
          'scrapeJRARaceResult',
          year as string,
          month as string,
          errorMessage
        ))
        response.status(400).send({success: false, error: errorMessage})
        return
      }

      const targetYear = parseInt(year as string)
      const targetMonth = parseInt(month as string)
      const targetDay = parseInt(day as string)
      
      const url = generateJRARaceResultUrl(targetYear, targetMonth, targetDay)
      const html = await fetchJRAHtmlWithPlaywright(url)
      const races = parseJRARaceResult(html, targetYear, targetMonth, targetDay)
      const savedCount = await saveRacesToFirestore(races)

      const executionTimeMs = Date.now() - startTime
      const message = `${targetYear}年${targetMonth}月${targetDay}日のJRAレース結果データの取得・保存が完了しました`
      
      // 成功時のログを保存
      await saveFunctionLog(createSuccessLog(
        'scrapeJRARaceResult',
        year as string,
        month as string,
        message,
        {
          racesCount: races.length,
          savedCount,
          url,
          executionTimeMs,
          day: targetDay
        }
      ))

      response.send({
        success: true,
        message,
        racesCount: races.length,
        savedCount,
        url,
        year: targetYear,
        month: targetMonth,
        day: targetDay,
        executionTimeMs
      })

    } catch (error) {
      const executionTimeMs = Date.now() - startTime
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      logger.error('JRA race result scraping failed', { error })
      
      // エラー時のログを保存
      const errorYear = (request.body || request.query).year as string
      const errorMonth = (request.body || request.query).month as string
      
      await saveFunctionLog(createErrorLog(
        'scrapeJRARaceResult',
        errorYear,
        errorMonth,
        errorMessage,
        { executionTimeMs }
      ))
      
      response.status(500).send({
        success: false,
        error: errorMessage,
        executionTimeMs
      })
    }
  }
)

/**
 * JRAカレンダーとレース結果データを一括取得・保存するCloud Function
 * 年と月を引数で受け取り、各日程のレース結果も含めて取得
 */
export const scrapeJRACalendarWithRaceResults = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1' },
  async (request, response) => {
    const startTime = Date.now()
    logger.info('JRA calendar with race results scraping function called')

    try {
      const year = request.query.year || request.body.year
      const month = request.query.month || request.body.month

      if (!year || !month) {
        const errorMessage = 'year and month parameters are required'
        
        await saveFunctionLog(createErrorLog(
          'scrapeJRACalendarWithRaceResults',
          year as string,
          month as string,
          errorMessage
        ))
        response.status(400).send({
          success: false,
          error: errorMessage
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
      
      // 2. カレンダーページから開催日をすべて抽出
      const $ = cheerio.load(calendarHtml)
      const raceDates = extractRaceDates($, targetYear, targetMonth)
      
      logger.info('Race dates extracted from calendar', { count: raceDates.length })
      
      // 3. 各日程のレース結果データを取得
      const allRaceResults: any[] = []
      const processedDates = new Set<string>()
      
      // カレンダーから抽出した開催日を優先して処理
      for (const raceDate of raceDates) {
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
      
      // 4. すべてのデータをFirestoreに保存
      const allRaces = [...calendarRaces, ...allRaceResults]
      const savedCount = await saveRacesToFirestore(allRaces)

      const executionTimeMs = Date.now() - startTime
      const message = `${targetYear}年${targetMonth}月のJRAカレンダーとレース結果データの取得・保存が完了しました`
      
      // 成功時のログを保存
      await saveFunctionLog(createSuccessLog(
        'scrapeJRACalendarWithRaceResults',
        year as string,
        month as string,
        message,
        {
          calendarRacesCount: calendarRaces.length,
          raceResultsCount: allRaceResults.length,
          totalRacesCount: allRaces.length,
          savedCount,
          calendarUrl,
          processedDates: Array.from(processedDates),
          executionTimeMs
        }
      ))

      response.send({
        success: true,
        message,
        calendarRacesCount: calendarRaces.length,
        raceResultsCount: allRaceResults.length,
        totalRacesCount: allRaces.length,
        savedCount,
        calendarUrl,
        processedDates: Array.from(processedDates),
        year: targetYear,
        month: targetMonth,
        executionTimeMs
      })

    } catch (error) {
      const executionTimeMs = Date.now() - startTime
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      logger.error('JRA calendar with race results scraping failed', { error })
      
      // エラー時のログを保存
      const errorYear = (request.body || request.query).year as string
      const errorMonth = (request.body || request.query).month as string
      
      await saveFunctionLog(createErrorLog(
        'scrapeJRACalendarWithRaceResults',
        errorYear,
        errorMonth,
        errorMessage,
        { executionTimeMs }
      ))
      
      response.status(500).send({
        success: false,
        error: errorMessage,
        executionTimeMs
      })
    }
  }
)

