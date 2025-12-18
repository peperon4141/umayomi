/**
 * Firestoreのracesコレクションのすべてのドキュメントを削除するスクリプト
 *
 * 使い方（エミュレータ例）:
 *   FIRESTORE_EMULATOR_HOST=127.0.0.1:8180 GCLOUD_PROJECT=umayomi-fbb2b \
 *   pnpm -F functions tsx scripts/delete_races_collection.ts
 */
import { getFirestore } from 'firebase-admin/firestore'
import { initializeApp } from 'firebase-admin/app'

const requireEnv = (name: string): string => {
  const value = process.env[name]
  if (!value) throw new Error(`${name} is required (no fallback).`)
  return value
}

// 誤ったプロジェクトを削除しないため、必須環境変数を明示チェック（fallback禁止）
requireEnv('FIRESTORE_EMULATOR_HOST')
requireEnv('GCLOUD_PROJECT')

initializeApp()

const db = getFirestore()

async function deleteRacesCollection() {
  try {
    console.log('racesコレクションのすべてのドキュメントを削除中...')
    
    const racesRef = db.collection('races')
    const snapshot = await racesRef.get()
    
    if (snapshot.empty) {
      console.log('racesコレクションにはドキュメントがありません')
      return
    }
    
    console.log(`${snapshot.size}件のドキュメントが見つかりました`)
    
    // バッチで削除（500件ずつ）
    const batchSize = 500
    let deletedCount = 0
    
    for (let i = 0; i < snapshot.docs.length; i += batchSize) {
      const batch = db.batch()
      const docs = snapshot.docs.slice(i, i + batchSize)
      
      docs.forEach(doc => {
        batch.delete(doc.ref)
      })
      
      await batch.commit()
      deletedCount += docs.length
      console.log(`${deletedCount}件のドキュメントを削除しました`)
    }
    
    console.log(`完了: ${deletedCount}件のドキュメントを削除しました`)
  } catch (error) {
    console.error('エラーが発生しました:', error)
    throw error
  }
}

// スクリプトを実行
deleteRacesCollection()
  .then(() => {
    console.log('削除処理が完了しました')
    process.exit(0)
  })
  .catch((error) => {
    console.error('削除処理でエラーが発生しました:', error)
    process.exit(1)
  })

