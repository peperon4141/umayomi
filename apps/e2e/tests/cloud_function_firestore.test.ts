import { test, expect } from '@playwright/test'
import { initializeApp, getApps } from 'firebase-admin/app'

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
  test.skip('scrapeJRACalendar関数を呼び出してデータを取得できる', async ({ request }) => {
    // スキップ理由: 実際のスクレイピングは重く、外部サイトに依存するため
    test.setTimeout(15000) // 15秒に短縮（実際は約6秒）
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendar?year=2025&month=10')

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

  test('scrapeJRARaceResult関数を呼び出してレース結果データを取得できる', async ({ request }) => {
    test.setTimeout(15000) // 15秒に短縮（実際は約6秒）
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRARaceResult?year=2025&month=10&day=13')

    expect(response.status()).toBe(200)
    
    const data = await response.json()
    // ✅ 良い例: 1つのオブジェクトを1つのexpectで検証
    expect(data).toEqual({
      success: true,
      message: expect.stringContaining('2025年10月13日のJRAレース結果データの取得・保存が完了しました'),
      racesCount: 24, // 2025年10月13日のレース数は24レースで固定
      savedCount: 24,  // 保存されたレース数も24レースで固定
      url: 'https://www.jra.go.jp/keiba/calendar2025/2025/10/1013.html',
      year: 2025,
      month: 10,
      day: 13,
      executionTimeMs: expect.any(Number) // 実行時間は変動するためany(Number)で検証
    })
    
    // // Firebase Admin SDKを使用してFirestoreのデータを検証
    // const racesSnapshot = await db.collection('races').get()
    // expect(racesSnapshot.size).toBeGreaterThan(0)
    
    // // 2025年10月13日のレースデータが存在することを確認
    // const raceDocs = racesSnapshot.docs.filter(doc => 
    //   doc.id.includes('2025-10-13') && doc.data().venue
    // )
    // expect(raceDocs.length).toBeGreaterThan(0)
    
    // // ✅ 良い例: レースデータの構造を1つのexpectで検証
    // const raceDoc = raceDocs[0]
    // const raceData = raceDoc.data()
    
    // // 2025年10月13日京都競馬場の具体的な値を検証
    // expect(raceData).toEqual({
    //   raceName: expect.stringMatching(/^(2歳未勝利|3歳未勝利|4歳以上未勝利|新馬|条件|特別|重賞|G[1-3]|J[G1-3]|地方競馬|障害)/), // 具体的なレース名パターン
    //   venue: '京都', // 2025年10月13日は京都競馬場で確定
    //   raceNumber: expect.any(Number),
    //   distance: expect.any(Number),
    //   surface: expect.stringMatching(/^(芝|ダ|障)$/), // 馬場種別（略称）
    //   date: expect.any(Object), // Firestore Timestamp
    //   startTime: expect.any(Object), // Firestore Timestamp
    //   createdAt: expect.any(Object), // Firestore Timestamp
    //   updatedAt: expect.any(Object), // Firestore Timestamp
    //   scrapedAt: expect.any(Object) // Firestore Timestamp
    // })
    
    // // 2025年10月13日東京競馬場の具体的な値の検証
    // expect(raceData.raceNumber).toBeGreaterThanOrEqual(1)
    // expect(raceData.raceNumber).toBeLessThanOrEqual(12)
    // expect(raceData.distance).toBeGreaterThanOrEqual(1000)
    // expect(raceData.distance).toBeLessThanOrEqual(3600)
    
    // // 具体的なレース番号と距離の検証（2025年10月13日東京競馬場）
    // expect([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]).toContain(raceData.raceNumber)
    // expect([1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 3000, 3200, 3600]).toContain(raceData.distance)
    
    // // Function Logも検証
    // const functionLogsSnapshot = await db.collection('functions_log').get()
    // expect(functionLogsSnapshot.size).toBeGreaterThan(0)
    
    // // scrapeJRARaceResultのログが存在することを確認
    // const functionLogs = functionLogsSnapshot.docs.filter(doc => 
    //   doc.data().functionName === 'scrapeJRARaceResult'
    // )
    // expect(functionLogs.length).toBeGreaterThan(0)
    
    // // ✅ 良い例: Function Logの構造を1つのexpectで検証
    // const functionLog = functionLogs[0]
    // const logData = functionLog.data()
    
    // expect(logData).toEqual({
    //   functionName: 'scrapeJRARaceResult',
    //   year: '2025',
    //   month: '10',
    //   success: true,
    //   message: expect.stringContaining('2025年10月13日のJRAレース結果データの取得・保存が完了しました'),
    //   additionalData: expect.objectContaining({
    //     racesCount: 24,
    //     savedCount: 24,
    //     url: 'https://www.jra.go.jp/keiba/calendar2025/2025/10/1013.html',
    //     day: 13,
    //     executionTimeMs: expect.any(Number)
    //   }),
    //   timestamp: expect.any(Object), // Firestore Timestamp
    //   createdAt: expect.any(Object) // Firestore Timestamp
    // })
    
    // // 具体的な値の検証
    // expect(logData.additionalData.executionTimeMs).toBeGreaterThan(0)
    // expect(logData.additionalData.executionTimeMs).toBeLessThan(10000) // 10秒以内
    // expect(logData.additionalData.racesCount).toBe(24)
    // expect(logData.additionalData.savedCount).toBe(24)
    // expect(logData.additionalData.day).toBe(13)
    
    // // Cloud FunctionsのレスポンスでFirestoreへの保存が成功したことを確認
    // // savedCountがracesCountと同じであることで、全レースが正常に保存されたことを検証
    // expect(data.savedCount).toBe(data.racesCount)
  })

  test.skip('scrapeJRACalendarWithRaceResults関数を呼び出してカレンダーとレース結果データを一括取得できる', async ({ request }) => {
    // スキップ理由: 実際のスクレイピングは重く（45秒）、外部サイトに依存するため
    test.setTimeout(50000) // 50秒に短縮（実際は約45秒）
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendarWithRaceResults?year=2025&month=10')

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
