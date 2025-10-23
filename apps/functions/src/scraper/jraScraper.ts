import { logger } from 'firebase-functions'
import { chromium } from 'playwright'
import { getRaceDayLinks } from './calendarScraper'
import { getRaceDayData } from './raceDayScraper'
import type { JRARaceData } from '../../../shared/jra'

/**
 * JRAスクレイピングメイン関数
 */
export async function scrapeJRAData(): Promise<JRARaceData[]> {
  let browser = null
  
  try {
    // Playwrightブラウザを起動
    browser = await chromium.launch({ 
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    })
    
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    const page = await context.newPage()
    
    // JRAの10月開催日程ページにアクセス
    const url = 'https://www.jra.go.jp/keiba/calendar/oct.html'
    logger.info('Accessing JRA calendar website', { url })
    
    // アクセスしたURLの履歴をログに記録
    logger.info('JRA scraping URL history', { 
      accessedUrl: url,
      timestamp: new Date().toISOString(),
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    // 開催日程ページから個別開催日のリンクを取得
    const raceDayLinks = await getRaceDayLinks(page, url)

    const races = []

    // 各開催日ページを処理
    for (const dayLink of raceDayLinks) {
      try {
        const dayRaces = await getRaceDayData(page, dayLink.href!)
        if (dayRaces && dayRaces.length > 0) {
          races.push(...dayRaces)
          logger.info('Scraped race day', { day: dayLink.text, racesCount: dayRaces.length })
        }
      } catch (error) {
        logger.error('Error scraping race day', { 
          dayLink: dayLink.text, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        })
      }
    }

    logger.info('JRA scraping completed', { racesCount: races.length })
    return races

  } catch (error) {
    logger.error('JRA scraping failed', { 
      error: error instanceof Error ? error.message : 'Unknown error' 
    })
    throw error
  } finally {
    if (browser) {
      await browser.close()
    }
  }
}

