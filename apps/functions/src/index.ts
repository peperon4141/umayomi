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
 * 検証用のHelloWorld関数
 */
export const helloWorld = onRequest(
  { timeoutSeconds: 30 },
  async (request, response) => {
    logger.info('HelloWorld function called')
    
    response.send({
      success: true,
      message: 'HelloWorld',
      timestamp: new Date().toISOString()
    })
  }
)

/**
 * JRAレース結果データを取得・保存するCloud Function
 * 年、月、日を引数で受け取る
 */
export const scrapeJRARaceResult = onRequest(
  { timeoutSeconds: 300, memory: '1GiB' },
  async (request, response) => {
    logger.info('JRA race result scraping function called')

    try {
      const { year, month, day } = request.query

      if (!year || !month || !day) {
        response.status(400).send({
          success: false,
          error: 'year, month and day parameters are required'
        })
        return
      }

      const targetYear = parseInt(year as string)
      const targetMonth = parseInt(month as string)
      const targetDay = parseInt(day as string)
      
      const url = generateJRARaceResultUrl(targetYear, targetMonth, targetDay)
      const html = await fetchJRAHtmlWithPlaywright(url)
      const races = parseJRARaceResult(html, targetYear, targetMonth, targetDay)
      const savedCount = await saveRacesToFirestore(races)

      response.send({
        success: true,
        message: `${targetYear}年${targetMonth}月${targetDay}日のJRAレース結果データの取得・保存が完了しました`,
        racesCount: races.length,
        savedCount,
        url,
        year: targetYear,
        month: targetMonth,
        day: targetDay
      })

    } catch (error) {
      logger.error('JRA race result scraping failed', { error })
      response.status(500).send({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }
)

