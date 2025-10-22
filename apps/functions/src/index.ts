import { onRequest } from 'firebase-functions/v2/https'
import { logger } from 'firebase-functions'
import { chromium } from 'playwright'
import { initializeApp } from 'firebase-admin/app'
import { getFirestore, Timestamp } from 'firebase-admin/firestore'

// Firebase Admin SDKを初期化
initializeApp()
const db = getFirestore()

/**
 * HelloWorld Cloud Function
 * TDDで作成されたシンプルな関数
 */
export const helloWorld = onRequest((request, response) => {
  logger.info('HelloWorld function called', { 
    method: request.method,
    url: request.url 
  })
  
  response.send('Hello World!')
})

/**
 * JRAスクレイピング Cloud Function
 * Playwrightを使用してJRAのレース結果を取得
 */
export const scrapeJRAData = onRequest(
  { timeoutSeconds: 300, memory: '1GiB' },
  async (request, response) => {
    logger.info('JRA scraping function called', { 
      method: request.method,
      url: request.url 
    })

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
      
      // JRAのレース結果ページにアクセス（2024年8月のデータを使用）
      const url = 'https://www.jra.go.jp/keiba/result/202408/'
      logger.info('Accessing JRA website', { url })
      
      // アクセスしたURLの履歴をログに記録
      logger.info('JRA scraping URL history', { 
        accessedUrl: url,
        timestamp: new Date().toISOString(),
        userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
      })
      
      await page.goto(url, { waitUntil: 'networkidle' })
      
      // レース結果のリンクを取得
      const raceLinks = await page.$$eval('a[href*="/result/"]', links => 
        links.map(link => ({
          href: link.getAttribute('href'),
          text: link.textContent?.trim() || ''
        })).filter(link => link.href && link.text)
      )

      logger.info('Found race links', { count: raceLinks.length })

      const races = []

      // 各レース結果ページを処理
      for (const link of raceLinks) {
        try {
          const raceData = await scrapeRaceDetail(page, link.href!)
          if (raceData) {
            races.push(raceData)
            logger.info('Scraped race data', { raceName: raceData.raceName })
          }
        } catch (error) {
          logger.error('Error scraping race', { 
            raceLink: link.text, 
            error: error instanceof Error ? error.message : 'Unknown error' 
          })
        }
      }

      logger.info('JRA scraping completed', { racesCount: races.length })

      // Firestoreに保存
      const savedCount = await saveRacesToFirestore(races)
      logger.info('Races saved to Firestore', { savedCount })

      response.send({
        success: true,
        message: 'JRAデータのスクレイピングが完了しました',
        racesCount: races.length,
        savedCount: savedCount,
        races: races
      })

    } catch (error) {
      logger.error('JRA scraping failed', { 
        error: error instanceof Error ? error.message : 'Unknown error' 
      })
      
      response.status(500).send({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    } finally {
      if (browser) {
        await browser.close()
      }
    }
  }
)

/**
 * 個別レースの詳細データを取得
 */
async function scrapeRaceDetail(page: any, raceUrl: string) {
  try {
    // 相対URLを絶対URLに変換
    const fullUrl = raceUrl.startsWith('http') ? raceUrl : `https://www.jra.go.jp${raceUrl}`
    await page.goto(fullUrl, { waitUntil: 'networkidle' })

    // レース情報を取得
    const raceInfo = await page.evaluate(() => {
      // 日付を取得
      const dateElement = document.querySelector('.race-date')
      const dateText = dateElement?.textContent?.trim() || ''
      
      // 競馬場を取得
      const racecourseElement = document.querySelector('.racecourse-name')
      const racecourse = racecourseElement?.textContent?.trim() || ''
      
      // レース名を取得
      const raceNameElement = document.querySelector('.race-name')
      const raceName = raceNameElement?.textContent?.trim() || ''
      
      // レース番号を取得
      const raceNumberElement = document.querySelector('.race-number')
      const raceNumberText = raceNumberElement?.textContent?.trim() || ''
      const raceNumber = parseInt(raceNumberText.replace('R', '')) || 0
      
      // グレードを取得
      const gradeElement = document.querySelector('.grade')
      const grade = gradeElement?.textContent?.trim() || '条件'
      
      // コース情報を取得
      const courseElement = document.querySelector('.course-info')
      const courseText = courseElement?.textContent?.trim() || ''
      const surface = courseText.includes('芝') ? '芝' : courseText.includes('ダート') ? 'ダート' : '障害'
      const distance = parseInt(courseText.match(/(\d+)m/)?.[1] || '0') || 0
      
      // 天候・馬場状態を取得
      const weatherElement = document.querySelector('.weather')
      const weather = weatherElement?.textContent?.trim() || '晴'
      
      const trackElement = document.querySelector('.track-condition')
      const trackCondition = trackElement?.textContent?.trim() || '良'
      
      // レース結果を取得
      const resultRows = document.querySelectorAll('.result-table tbody tr')
      const results = Array.from(resultRows).map((row, index) => {
        const cells = row.querySelectorAll('td')
        if (cells.length < 4) return null
        
        return {
          rank: index + 1,
          horseName: cells[1]?.textContent?.trim() || '',
          jockey: cells[2]?.textContent?.trim() || '',
          odds: parseFloat(cells[3]?.textContent?.trim() || '0')
        }
      }).filter(Boolean)

      return {
        date: dateText,
        racecourse,
        raceNumber,
        raceName,
        grade,
        surface,
        distance,
        weather,
        trackCondition,
        results
      }
    })

    if (!raceInfo || !raceInfo.results.length) {
      return null
    }

    // 日付をパース
    const date = parseDate(raceInfo.date)
    if (!date) {
      logger.warn('Failed to parse date', { date: raceInfo.date })
      return null
    }

    // Raceオブジェクトを作成
    const race = {
      id: `jra-${date.getTime()}-${raceInfo.raceNumber}`,
      date: date,
      racecourse: raceInfo.racecourse,
      raceNumber: raceInfo.raceNumber,
      raceName: raceInfo.raceName,
      grade: raceInfo.grade,
      surface: raceInfo.surface as '芝' | 'ダート' | '障害',
      distance: raceInfo.distance,
      weather: raceInfo.weather,
      trackCondition: raceInfo.trackCondition,
      results: raceInfo.results
    }

    return race

  } catch (error) {
    logger.error('Error scraping race detail', { 
      raceUrl, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    })
    return null
  }
}

/**
 * 日付文字列をDateオブジェクトに変換
 */
function parseDate(dateStr: string): Date | null {
  try {
    // "2025年10月5日" 形式をパース
    const match = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/)
    if (match) {
      const year = parseInt(match[1])
      const month = parseInt(match[2]) - 1 // JavaScriptの月は0ベース
      const day = parseInt(match[3])
      return new Date(year, month, day)
    }
    
    // その他の形式も試行
    const date = new Date(dateStr)
    return isNaN(date.getTime()) ? null : date
  } catch {
    return null
  }
}

/**
 * レースデータをFirestoreに保存
 */
async function saveRacesToFirestore(races: any[]): Promise<number> {
  if (!races.length) return 0

  const batch = db.batch()
  let savedCount = 0

  for (const race of races) {
    try {
      // 既存データとの重複チェック
      const existingRace = await db.collection('races').doc(race.id).get()
      
      if (existingRace.exists) {
        logger.info('Race already exists, skipping', { raceId: race.id })
        continue
      }

      // Firestore用のデータ形式に変換
      const raceData = {
        id: race.id,
        date: Timestamp.fromDate(race.date),
        racecourse: race.racecourse,
        raceNumber: race.raceNumber,
        raceName: race.raceName,
        grade: race.grade,
        surface: race.surface,
        distance: race.distance,
        weather: race.weather,
        trackCondition: race.trackCondition,
        results: race.results,
        createdAt: Timestamp.now(),
        updatedAt: Timestamp.now()
      }

      // バッチに追加
      const raceRef = db.collection('races').doc(race.id)
      batch.set(raceRef, raceData)
      savedCount++

    } catch (error) {
      logger.error('Error preparing race for batch', { 
        raceId: race.id, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      })
    }
  }

  if (savedCount > 0) {
    try {
      await batch.commit()
      logger.info('Batch write completed', { savedCount })
    } catch (error) {
      logger.error('Batch write failed', { 
        error: error instanceof Error ? error.message : 'Unknown error' 
      })
      throw error
    }
  }

  return savedCount
}
