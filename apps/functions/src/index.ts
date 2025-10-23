import { onRequest } from 'firebase-functions/v2/https'
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
      const docRef = db.collection('races').doc()
      batch.set(docRef, {
        ...race,
        date: Timestamp.fromDate(race.date),
        scrapedAt: Timestamp.fromDate(race.scrapedAt)
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