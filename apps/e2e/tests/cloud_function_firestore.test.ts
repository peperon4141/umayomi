import { test, expect } from '@playwright/test'
import { initializeApp, getApps } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'
import { getFirestore } from 'firebase-admin/firestore'

// Firebase Emulator用の環境変数を設定（開発時のみ）
process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
process.env.FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9199'
process.env.GCLOUD_PROJECT = 'umayomi-fbb2b'

// Firebase Admin SDKの初期化
if (!getApps().length) {
  initializeApp({
    projectId: 'umayomi-fbb2b',
    // Firebase Emulatorを使用するため、認証情報は不要
  })
}

// // Cloud Functionsテスト用の設定
// test.use({
//   actionTimeout: 300000, // 5分のタイムアウト
// })

test.describe('Cloud Functions', () => {
  test('uploadModel関数でモデルをアップロードできる', async ({ request }) => {
    const adminAuth = getAuth()
    const db = getFirestore()

    const email = 'test@example.com'
    const password = 'password123'

    let uid: string
    try {
      uid = (await adminAuth.getUserByEmail(email)).uid
    } catch {
      uid = (await adminAuth.createUser({ email, password, emailVerified: true })).uid
    }

    const customToken = await adminAuth.createCustomToken(uid)

    const signInRes = await request.post('http://127.0.0.1:9199/identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=fake-api-key', {
      data: { token: customToken, returnSecureToken: true }
    })
    expect(signInRes.ok()).toBe(true)
    const signInJson = await signInRes.json()
    const idToken = signInJson.idToken as string
    expect(typeof idToken).toBe('string')

    const modelName = 'rank_model_upload_test'
    const storagePath = 'models/rank_model_upload_test.txt'
    const contentBase64 = Buffer.from('dummy model content', 'utf8').toString('base64')

    const uploadRes = await request.post('http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/uploadModel', {
      headers: { Authorization: `Bearer ${idToken}` },
      data: {
        fileName: 'rank_model_upload_test.txt',
        contentBase64,
        modelName,
        storagePath,
        version: 'test',
        description: 'e2e upload test',
        trainingDate: '2025-12-18'
      }
    })

    expect(uploadRes.ok()).toBe(true)
    const uploadJson = await uploadRes.json()
    expect(uploadJson.success).toBe(true)
    expect(uploadJson.modelName).toBe(modelName)
    expect(uploadJson.storagePath).toBe(storagePath)

    const modelDoc = await db.collection('models').doc(modelName).get()
    expect(modelDoc.exists).toBe(true)
    expect(modelDoc.data()).toMatchObject({
      model_name: modelName,
      storage_path: storagePath
    })
  })

  test.skip('scrapeJRACalendar関数を呼び出してデータを取得できる', async ({ request }) => {
    // スキップ理由: 実際のスクレイピングは重く、外部サイトに依存するため
    test.setTimeout(15000) // 15秒に短縮（実際は約6秒）
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/scrapeJRACalendar?year=2025&month=10')

    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.message).toContain('2025年10月のJRAデータの取得・保存が完了しました')
    expect(data.racesCount).toBeGreaterThan(0)
    expect(data.savedCount).toBeGreaterThan(0)
    expect(data.url).toBe('https://www.jra.go.jp/keiba/calendar2025/oct.html')
    expect(data.year).toBe(2025)
    expect(data.month).toBe(10)
  })

  test.skip('scrapeJRACalendarWithRaceResults関数を呼び出してカレンダーとレース結果データを一括取得できる', async ({ request }) => {
    // スキップ理由: 実際のスクレイピングは重く（45秒）、外部サイトに依存するため
    test.setTimeout(50000) // 50秒に短縮（実際は約45秒）
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/scrapeJRACalendarWithRaceResults?year=2025&month=10')

    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.message).toContain('2025年10月のJRAカレンダーとレース結果データの取得・保存が完了しました')
    expect(data.calendarRacesCount).toBeGreaterThan(0)
    expect(data.raceResultsCount).toBeGreaterThan(0)
    expect(data.totalRacesCount).toBe(data.calendarRacesCount + data.raceResultsCount)
    expect(data.savedCount).toBeGreaterThan(0)
    expect(data.calendarUrl).toBe('https://www.jra.go.jp/keiba/calendar2025/oct.html')
    expect(data.processedDates).toBeDefined()
    expect(data.year).toBe(2025)
    expect(data.month).toBe(10)
  })
})
