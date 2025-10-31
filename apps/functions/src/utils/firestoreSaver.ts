import { getFirestore } from 'firebase-admin/firestore'
import { logger } from 'firebase-functions'

// // Firestoreインスタンスをキャッシュ
// let dbInstance: FirebaseFirestore.Firestore | null = null

// /**
//  * Firestoreインスタンスを取得（遅延初期化）
//  */
// function getDb() {
//   if (!dbInstance) {
//     // 開発環境でFirestore Emulatorに接続
//     const isDevelopment = process.env.NODE_ENV === 'development' || 
//                          process.env.FUNCTIONS_EMULATOR === 'true' ||
//                          process.env.MODE === 'development'
    
//     if (isDevelopment) {
//       // Firebase Admin SDKの環境変数を設定（getFirestoreより前に設定）
//       process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
//       logger.info('Firestore Emulator環境変数を設定しました (firestoreSaver)', {
//         firestoreEmulatorHost: process.env.FIRESTORE_EMULATOR_HOST,
//         nodeEnv: process.env.NODE_ENV,
//         functionsEmulator: process.env.FUNCTIONS_EMULATOR,
//         mode: process.env.MODE
//       })
//     }
    
//     dbInstance = getFirestore()
    
//     if (isDevelopment && !process.env.FIRESTORE_EMULATOR_HOST) {
//       logger.warn('Firestore Emulator環境変数が設定されていません (firestoreSaver)')
//     }
//   }
  
//   return dbInstance
// }

/**
 * レースデータをFirestoreに保存
 */
export async function saveRacesToFirestore(races: any[]): Promise<number> {
  if (!races.length) {
    logger.info('No races to save')
    return 0
  }
  
  try {
    const db = getFirestore()
    const batch = db.batch()
    
    races.forEach(race => {
      // venueをracecourseにマッピング（後方互換性のため両方を確認）
      const venue = race.venue || race.racecourse
      const raceId = `${race.date.toISOString().split('T')[0]}_${venue}_${race.raceNumber}`
      const docRef = db.collection('races').doc(raceId)
      
      const raceData = {
        ...race,
        // venueをracecourseに統一
        racecourse: venue,
        venue: undefined, // 古いフィールドを削除
        date: race.date,
        scrapedAt: race.scrapedAt,
        createdAt: new Date(),
        updatedAt: new Date()
      }
      
      // undefinedフィールドを削除
      Object.keys(raceData).forEach(key => {
        if (raceData[key] === undefined) {
          delete raceData[key]
        }
      })
      
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
