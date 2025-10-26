import { getFirestore } from 'firebase-admin/firestore'
import { logger } from 'firebase-functions'

/**
 * Firestoreインスタンスを取得（遅延初期化）
 */
function getDb() {
  return getFirestore()
}

/**
 * レースデータをFirestoreに保存
 */
export async function saveRacesToFirestore(races: any[]): Promise<number> {
  if (!races.length) {
    logger.info('No races to save')
    return 0
  }
  
  try {
    const db = getDb()
    const batch = db.batch()
    
    races.forEach(race => {
      const raceId = `${race.date.toISOString().split('T')[0]}_${race.venue}_${race.raceNumber}`
      const docRef = db.collection('races').doc(raceId)
      
      const raceData = {
        ...race,
        date: race.date,
        scrapedAt: race.scrapedAt,
        createdAt: new Date(),
        updatedAt: new Date()
      }
      
      batch.set(docRef, raceData)
    })
    
    await batch.commit()
    logger.info('Races saved to Firestore successfully', { 
      savedCount: races.length,
      collection: 'races'
    })
    
    return races.length
    
  } catch (error) {
    logger.error('Failed to save races to Firestore', { error })
    throw new Error(`Firestore save failed: ${error}`)
  }
}
