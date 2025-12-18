import { getFirestore } from 'firebase-admin/firestore'
import { logger } from 'firebase-functions'
import { generateRaceKey } from './raceKeyGenerator'

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
    
    // race_keyの重複をチェック
    const raceKeyCounts: { [key: string]: number } = {}
    const duplicateRaceKeys: string[] = []
    
    races.forEach((race, index) => {
      // venueをracecourseにマッピング（後方互換性のため両方を確認）
      const venue = race.venue || race.racecourse
      if (!venue) 
        throw new Error(
          `venue or racecourse is required but both were null or undefined. ` +
          `race index: ${index}, raceNumber: ${race.raceNumber}, round: ${race.round}`
        )
      
      const racecourse = venue
      
      // race_id（JRDB原典キー）を生成
      const raceDate = race.raceDate || race.date // 後方互換性のため
      if (!raceDate) 
        throw new Error(
          `raceDate or date is required but both were null or undefined. ` +
          `race index: ${index}, venue: ${venue}, raceNumber: ${race.raceNumber}, round: ${race.round}`
        )
      
      
      // roundがnullの場合はエラーを投げる（generateRaceKeyが必須としている）
      if (race.round == null) {
        logger.warn('round is null, skipping race', {
          raceIndex: index,
          venue,
          raceNumber: race.raceNumber,
          raceDate: raceDate instanceof Date ? raceDate.toISOString().split('T')[0] : raceDate
        })
        return // このレースをスキップ（レース結果ページから取得したデータで上書きされる）
      }

      // day（開催日目）がない場合はスキップ（fallback禁止）
      if (race.day == null) {
        logger.warn('day is null, skipping race', {
          raceIndex: index,
          venue,
          raceNumber: race.raceNumber,
          raceDate: raceDate instanceof Date ? raceDate.toISOString().split('T')[0] : raceDate
        })
        return
      }
      
      const race_id = generateRaceKey({
        racecourse,
        raceNumber: race.raceNumber,
        round: race.round,
        day: race.day
      })
      
      // 重複チェック（最初の重複時に詳細ログを出力）
      const count = (raceKeyCounts[race_id] || 0) + 1
      raceKeyCounts[race_id] = count
      
      if (count === 2) {
        // 最初の重複を検出した時点で詳細ログを出力
        const existingRace = races.find((r, i) => {
          if (i >= index) return false
          const existingKey = generateRaceKey({
            racecourse: r.venue || r.racecourse,
            raceNumber: r.raceNumber,
            round: r.round,
            day: r.day
          })
          return existingKey === race_id
        })
        
        if (existingRace) {
          const existingVenue = existingRace.venue || existingRace.racecourse
          const existingDate = existingRace.raceDate || existingRace.date
          const currentVenue = race.venue || race.racecourse
          const currentDate = race.raceDate || race.date
          
          logger.warn('Duplicate race_key detected - first occurrence', {
            race_id,
            existingRace: {
              raceDate: existingDate,
              venue: existingVenue,
              raceNumber: existingRace.raceNumber,
              round: existingRace.round,
              day: existingRace.day
            },
            currentRace: {
              raceDate: currentDate,
              venue: currentVenue,
              raceNumber: race.raceNumber,
              round: race.round,
              day: race.day
            }
          })
        }
      }
      
      if (count > 1 && !duplicateRaceKeys.includes(race_id)) duplicateRaceKeys.push(race_id)
      
      // 日付から年と月を取得
      let year: number
      let month: number
      
      if (raceDate instanceof Date) {
        year = raceDate.getFullYear()
        month = raceDate.getMonth() + 1
      } else if (raceDate && typeof raceDate === 'object' && 'toDate' in raceDate) {
        // Firestore Timestamp
        const date = raceDate.toDate()
        year = date.getFullYear()
        month = date.getMonth() + 1
      } else if (raceDate && typeof raceDate === 'object' && 'seconds' in raceDate) {
        // Firestore Timestamp形式
        const date = new Date(raceDate.seconds * 1000)
        if (isNaN(date.getTime())) 
          throw new Error(
            `Invalid Firestore Timestamp: ${JSON.stringify(raceDate)}. ` +
            `race index: ${index}, venue: ${venue}, raceNumber: ${race.raceNumber}, round: ${race.round}`
          )
        
        year = date.getFullYear()
        month = date.getMonth() + 1
      } else {
        // Dateオブジェクトに変換を試みる
        const date = new Date(raceDate)
        if (isNaN(date.getTime())) 
          throw new Error(
            `Invalid date value: ${raceDate}. ` +
            `race index: ${index}, venue: ${venue}, raceNumber: ${race.raceNumber}, round: ${race.round}`
          )
        
        year = date.getFullYear()
        month = date.getMonth() + 1
      }
      
      // 年と月の妥当性チェック
      if (!year || year < 1900 || year > 2100) 
        throw new Error(
          `Invalid year: ${year}. Year must be between 1900 and 2100. ` +
          `race index: ${index}, venue: ${venue}, raceNumber: ${race.raceNumber}, round: ${race.round}`
        )
      
      if (!month || month < 1 || month > 12) 
        throw new Error(
          `Invalid month: ${month}. Month must be between 1 and 12. ` +
          `race index: ${index}, venue: ${venue}, raceNumber: ${race.raceNumber}, round: ${race.round}`
        )
      
      
      // 年別名前空間: racesByYear/{year}/races/{race_id}
      const docRef = db.collection('racesByYear').doc(String(year)).collection('races').doc(race_id)
      
      const raceData = {
        ...race,
        race_id, // 明示的なID
        race_key: race_id, // 後方互換性: UI/型がrace_keyを参照しているため
        // venueをracecourseに統一
        racecourse,
        venue: undefined, // 古いフィールドを削除
        year,  // 年フィールドを追加
        month, // 月フィールドを追加
        raceDate: raceDate, // raceDateに統一
        date: undefined, // 古いフィールドを削除
        scrapedAt: race.scrapedAt,
        createdAt: new Date(),
        updatedAt: new Date()
      }
      
      // undefinedフィールドを削除
      Object.keys(raceData).forEach(key => {
        if (raceData[key] === undefined) delete raceData[key]
      })
      
      batch.set(docRef, raceData)
    })
    
    // 重複がある場合は警告を出力
    if (duplicateRaceKeys.length > 0) 
      logger.warn('Duplicate race_keys detected', {
        duplicateCount: duplicateRaceKeys.length,
        duplicateKeys: duplicateRaceKeys,
        totalRaces: races.length,
        uniqueRaceKeys: Object.keys(raceKeyCounts).length
      })
    
    
    await batch.commit()
    
    logger.info('Races saved to Firestore successfully', { 
      savedCount: races.length,
      uniqueRaceKeys: Object.keys(raceKeyCounts).length,
      duplicateRaceKeys: duplicateRaceKeys.length,
      collection: 'racesByYear/{year}/races'
    })
    
    return Object.keys(raceKeyCounts).length // 重複を考慮してユニークなrace_keyの数を返す
    
  } catch (error) {
    logger.error('Failed to save races to Firestore', { error })
    throw new Error(`Firestore save failed: ${error}`)
  }
}
