import { logger } from 'firebase-functions'
import { fetchJRAHtmlWithPlaywright } from '../utils/htmlFetcher'
import { parseJRACalendar, extractRaceDates } from './parser/calendarParser'
import * as cheerio from 'cheerio'
import { parseJRARaceResult } from './parser/raceResultParser'
import { saveRacesToFirestore } from '../utils/firestoreSaver'
import { generateJRACalendarUrl, generateJRARaceResultUrl } from '../utils/urlGenerator'
import { saveFunctionLog, createSuccessLog, createErrorLog } from '../utils/functionLogSaver'

/**
 * JRAカレンダーデータを取得・保存する処理
 */
export async function handleScrapeJRACalendar(request: any, response: any): Promise<void> {
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
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined
    const errorName = error instanceof Error ? error.name : 'Unknown'
    const errorType = error?.constructor?.name || 'Unknown'
    
    // logger.errorにシリアライズ可能な形式でエラー情報を渡す
    try {
      logger.error('JRA scraping failed', {
        errorMessage,
        errorName,
        errorType,
        errorStack,
        executionTimeMs
      })
    } catch (logError) {
      // logger.error自体が失敗した場合は、より安全な方法でログを出力
      logger.error('JRA scraping failed', {
        errorMessage: String(error),
        executionTimeMs,
        logError: logError instanceof Error ? logError.message : String(logError)
      })
    }
    
    // エラー時のログを保存（エラーハンドリング内でのエラーを防ぐ）
    try {
      const errorYear = (request.body || request.query).year as string
      const errorMonth = (request.body || request.query).month as string
      
      await saveFunctionLog(createErrorLog(
        'scrapeJRACalendar',
        errorYear,
        errorMonth,
        errorMessage,
        { 
          executionTimeMs,
          errorStack,
          errorType
        }
      ))
    } catch (saveLogError) {
      // ログ保存の失敗は処理を停止させない
      logger.warn('Failed to save error log', {
        saveLogError: saveLogError instanceof Error ? saveLogError.message : String(saveLogError)
      })
    }
    
    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

/**
 * JRAレース結果データを取得・保存する処理
 */
export async function handleScrapeJRARaceResult(request: any, response: any): Promise<void> {
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
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined
    const errorName = error instanceof Error ? error.name : 'Unknown'
    const errorType = error?.constructor?.name || 'Unknown'
    
    // logger.errorにシリアライズ可能な形式でエラー情報を渡す
    try {
      logger.error('JRA race result scraping failed', {
        errorMessage,
        errorName,
        errorType,
        errorStack,
        executionTimeMs,
        year: request.query.year || request.body.year,
        month: request.query.month || request.body.month,
        day: request.query.day || request.body.day
      })
    } catch (logError) {
      // logger.error自体が失敗した場合は、より安全な方法でログを出力
      logger.error('JRA race result scraping failed', {
        errorMessage: String(error),
        executionTimeMs,
        logError: logError instanceof Error ? logError.message : String(logError)
      })
    }
    
    // エラー時のログを保存（エラーハンドリング内でのエラーを防ぐ）
    try {
      const errorYear = (request.body || request.query).year as string
      const errorMonth = (request.body || request.query).month as string
      
      await saveFunctionLog(createErrorLog(
        'scrapeJRARaceResult',
        errorYear,
        errorMonth,
        errorMessage,
        { 
          executionTimeMs,
          errorStack,
          errorType
        }
      ))
    } catch (saveLogError) {
      // ログ保存の失敗は処理を停止させない
      logger.warn('Failed to save error log', {
        saveLogError: saveLogError instanceof Error ? saveLogError.message : String(saveLogError)
      })
    }
    
    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

/**
 * JRAカレンダーとレース結果データを一括取得・保存する処理
 */
export async function handleScrapeJRACalendarWithRaceResults(request: any, response: any): Promise<void> {
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
        logger.info('Fetching race results for date', { date: dateKey, day, url: raceResultUrl })
        
        const raceResultHtml = await fetchJRAHtmlWithPlaywright(raceResultUrl)
        const raceResults = parseJRARaceResult(raceResultHtml, targetYear, targetMonth, day)
        
        allRaceResults.push(...raceResults)
        logger.info('Race results fetched for date', { date: dateKey, count: raceResults.length })
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        const errorStack = error instanceof Error ? error.stack : undefined
        
        logger.warn('Failed to fetch race results for date', { 
          date: dateKey, 
          error: errorMessage,
          stack: errorStack,
          errorType: error?.constructor?.name
        })
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
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined
    const errorName = error instanceof Error ? error.name : 'Unknown'
    const errorType = error?.constructor?.name || 'Unknown'
    
    // logger.errorにシリアライズ可能な形式でエラー情報を渡す
    try {
      logger.error('JRA calendar with race results scraping failed', {
        errorMessage,
        errorName,
        errorType,
        errorStack,
        executionTimeMs,
        year: request.query.year || request.body.year,
        month: request.query.month || request.body.month
      })
    } catch (logError) {
      // logger.error自体が失敗した場合は、より安全な方法でログを出力
      logger.error('JRA calendar with race results scraping failed', {
        errorMessage: String(error),
        executionTimeMs,
        logError: logError instanceof Error ? logError.message : String(logError)
      })
    }
    
    // エラー時のログを保存（エラーハンドリング内でのエラーを防ぐ）
    try {
      const errorYear = (request.body || request.query).year as string
      const errorMonth = (request.body || request.query).month as string
      
      await saveFunctionLog(createErrorLog(
        'scrapeJRACalendarWithRaceResults',
        errorYear,
        errorMonth,
        errorMessage,
        { 
          executionTimeMs,
          errorStack,
          errorType
        }
      ))
    } catch (saveLogError) {
      // ログ保存の失敗は処理を停止させない
      logger.warn('Failed to save error log', {
        saveLogError: saveLogError instanceof Error ? saveLogError.message : String(saveLogError)
      })
    }
    
    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

