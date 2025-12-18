/**
 * モデルメタデータをFirestoreエミュレーターに保存するスクリプト
 */

import { initializeApp } from 'firebase-admin/app'
import { getFirestore } from 'firebase-admin/firestore'

// エミュレーター環境を設定
process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
process.env.GCLOUD_PROJECT = 'umayomi-fbb2b'

// Firebase Admin SDKを初期化
initializeApp({
  projectId: 'umayomi-fbb2b'
})

const db = getFirestore()

async function saveModelMetadata() {
  const modelName = 'rank_model_202512111031_v1'
  const storagePath = 'models/rank_model_202512111031_v1.txt'
  const storageUrl = 'http://127.0.0.1:9198/umayomi-fbb2b.firebasestorage.app/models/rank_model_202512111031_v1.txt'
  
  const docRef = db.collection('models').doc(modelName)
  
  await docRef.set({
    model_name: modelName,
    storage_path: storagePath,
    storage_url: storageUrl,
    version: '1.0',
    description: 'Rank prediction model v1',
    training_date: '2025-12-11',
    created_at: new Date(),
    updated_at: new Date()
  }, { merge: true })
  
  console.log(`✓ モデルメタデータをFirestoreに保存しました: models/${modelName}`)
}

saveModelMetadata()
  .then(() => {
    console.log('完了')
    process.exit(0)
  })
  .catch((error) => {
    console.error('エラー:', error)
    process.exit(1)
  })

