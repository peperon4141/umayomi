/**
 * 既存のracesコレクションのドキュメントにyearとmonthフィールドを追加するスクリプト
 */

import { getFirestore } from 'firebase-admin/firestore'
import { logger } from 'firebase-functions'

/**
 * 既存のracesコレクションのドキュメントにyearとmonthフィールドを追加
 */
export async function addYearMonthToRaces(): Promise<void> {
  const db = getFirestore()
  const racesRef = db.collection('races')
  
  logger.info('既存のracesコレクションからyearとmonthフィールドを追加開始')
  
  try {
    // すべてのレースを取得
    const snapshot = await racesRef.get()
    
    if (snapshot.empty) {
      logger.info('racesコレクションにドキュメントがありません')
      return
    }
    
    logger.info(`処理対象: ${snapshot.size}件のドキュメント`)
    
    let processedCount = 0
    let skippedCount = 0
    let errorCount = 0
    
    // バッチ処理で更新
    let batch = db.batch()
    let batchCount = 0
    const maxBatchSize = 500
    
    for (const doc of snapshot.docs) {
      try {
        const data = doc.data()
        
        // yearとmonthフィールドが既に存在する場合はスキップ
        if (data.year && data.month) {
          skippedCount++
          continue
        }
        
        // dateフィールドから年と月を取得
        let year: number
        let month: number
        
        if (data.date) {
          if (data.date instanceof Date) {
            year = data.date.getFullYear()
            month = data.date.getMonth() + 1
          } else if (data.date && typeof data.date === 'object' && 'toDate' in data.date) {
            // Firestore Timestamp
            const date = data.date.toDate()
            year = date.getFullYear()
            month = date.getMonth() + 1
          } else if (data.date && typeof data.date === 'object' && 'seconds' in data.date) {
            // Firestore Timestamp形式
            const date = new Date(data.date.seconds * 1000)
            year = date.getFullYear()
            month = date.getMonth() + 1
          } else {
            logger.warn('dateフィールドの形式が不正です', { docId: doc.id, date: data.date })
            errorCount++
            continue
          }
        } else {
          logger.warn('dateフィールドが存在しません', { docId: doc.id })
          errorCount++
          continue
        }
        
        // yearとmonthフィールドを追加
        const docRef = racesRef.doc(doc.id)
        batch.update(docRef, {
          year,
          month,
          updatedAt: new Date()
        })
        
        batchCount++
        processedCount++
        
        // バッチサイズに達したらコミット
        if (batchCount >= maxBatchSize) {
          await batch.commit()
          logger.info(`バッチコミット: ${batchCount}件を更新`)
          batch = db.batch() // 新しいbatchを作成
          batchCount = 0
        }
      } catch (error) {
        logger.error('ドキュメント処理エラー', { docId: doc.id, error })
        errorCount++
      }
    }
    
    // 残りのバッチをコミット
    if (batchCount > 0) {
      await batch.commit()
      logger.info(`最終バッチコミット: ${batchCount}件を更新`)
    }
    
    logger.info('yearとmonthフィールドの追加が完了しました', {
      processedCount,
      skippedCount,
      errorCount,
      totalCount: snapshot.size
    })
    
  } catch (error) {
    logger.error('yearとmonthフィールドの追加に失敗しました', { error })
    throw error
  }
}

