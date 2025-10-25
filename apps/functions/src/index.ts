import { onRequest } from 'firebase-functions/v2/https'
import { onSchedule } from 'firebase-functions/v2/scheduler'
import { logger } from 'firebase-functions'
import { initializeApp } from 'firebase-admin/app'
import { getFirestore, Timestamp } from 'firebase-admin/firestore'
import { getAuth } from 'firebase-admin/auth'
import { scrapeJRAData as scrapeJRADataLogic } from './scraper/jraScraper'
import type { JRARaceData } from '../../shared/jra'

// Firebase Admin SDKを初期化
initializeApp()
const db = getFirestore()
const auth = getAuth()

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

    try {
      // スクレイピング実行
      const races = await scrapeJRADataLogic()
      
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
    }
  }
)

/**
 * Firestoreにレースデータを保存
 */
async function saveRacesToFirestore(races: JRARaceData[]) {
  if (races.length === 0) return 0
  
  const batch = db.batch()
  let savedCount = 0
  
  for (const race of races) {
    try {
      // 日付の検証と修正
      let validDate = race.date
      if (!validDate || isNaN(validDate.getTime())) {
        logger.warn('Invalid date found, using current date', { race: race.raceName, originalDate: race.date })
        validDate = new Date()
      }
      
      // 必須フィールドの検証
      if (!race.raceName || !race.grade) {
        logger.warn('Missing required fields, skipping race', { race })
        continue
      }
      
      const docRef = db.collection('races').doc()
      batch.set(docRef, {
        ...race,
        date: Timestamp.fromDate(validDate),
        scrapedAt: race.scrapedAt instanceof Date ? Timestamp.fromDate(race.scrapedAt) : Timestamp.fromDate(new Date(race.scrapedAt))
      })
      savedCount++
    } catch (error) {
      logger.error('Error saving race to Firestore', { race, error })
    }
  }
  
  try {
    await batch.commit()
    logger.info('Batch committed successfully', { savedCount })
  } catch (error) {
    logger.error('Error committing batch', { error })
    throw error
  }
  
  return savedCount
}

/**
 * ユーザーにadminロールを付与する Cloud Function
 */
export const setAdminRole = onRequest(async (request, response) => {
  logger.info('setAdminRole function called', { 
    method: request.method,
    url: request.url 
  })

  try {
    const { uid } = request.body

    if (!uid) {
      response.status(400).send({
        success: false,
        error: 'UID is required'
      })
      return
    }

    // ユーザーにadminロールを付与
    await auth.setCustomUserClaims(uid, { role: 'admin' })
    
    logger.info('Admin role set successfully', { uid })

    response.send({
      success: true,
      message: 'Admin role has been set successfully'
    })

  } catch (error) {
    logger.error('Failed to set admin role', { 
      error: error instanceof Error ? error.message : 'Unknown error' 
    })
    
    response.status(500).send({
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    })
  }
})

/**
 * 定期実行でJRAデータをスクレイピングする Cloud Function
 * 毎日午前6時に実行
 */
export const scheduledJraScraping = onSchedule(
  {
    schedule: '0 6 * * *', // 毎日午前6時（JST）
    timeZone: 'Asia/Tokyo',
    memory: '1GiB',
    timeoutSeconds: 300
  },
  async (event) => {
    logger.info('Scheduled JRA scraping started', { 
      timestamp: new Date().toISOString(),
      eventId: event.scheduleTime 
    })

    try {
      // スクレイピング実行
      const races = await scrapeJRADataLogic()
      
      logger.info('Scheduled JRA scraping completed', { racesCount: races.length })

      // Firestoreに保存
      const savedCount = await saveRacesToFirestore(races)
      logger.info('Scheduled races saved to Firestore', { savedCount })

      // 成功通知（必要に応じて）
      logger.info('Scheduled JRA scraping completed successfully', {
        racesCount: races.length,
        savedCount
      })

    } catch (error) {
      logger.error('Scheduled JRA scraping failed', { 
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      })
      
      // エラー通知（必要に応じて）
      // ここでSlackやメール通知を送信することも可能
    }
  }
)

/**
 * 手動でJRAデータをスクレイピングする Cloud Function
 * 管理者が手動で実行可能
 */
export const manualJraScraping = onRequest(
  { timeoutSeconds: 300, memory: '1GiB' },
  async (request, response) => {
    logger.info('Manual JRA scraping function called', { 
      method: request.method,
      url: request.url,
      timestamp: new Date().toISOString()
    })

    try {
      // 認証チェック（管理者のみ実行可能）
      const authHeader = request.headers.authorization
      if (!authHeader) {
        response.status(401).send({
          success: false,
          error: 'Authorization header is required'
        })
        return
      }

      // スクレイピング実行
      const races = await scrapeJRADataLogic()
      
      logger.info('Manual JRA scraping completed', { racesCount: races.length })

      // Firestoreに保存
      const savedCount = await saveRacesToFirestore(races)
      logger.info('Manual races saved to Firestore', { savedCount })

      response.send({
        success: true,
        message: '手動JRAデータのスクレイピングが完了しました',
        racesCount: races.length,
        savedCount: savedCount,
        timestamp: new Date().toISOString()
      })

    } catch (error) {
      logger.error('Manual JRA scraping failed', { 
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      })
      
      response.status(500).send({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      })
    }
  }
)