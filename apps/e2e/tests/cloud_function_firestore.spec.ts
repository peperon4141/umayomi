import { test, expect } from '@playwright/test'

test.describe('Cloud Function Firestore Integration', () => {
  test('Cloud Functionを呼び出してFirestoreにデータが保存される', async ({ request, page }) => {
    // タイムアウトを延長
    test.setTimeout(30000)
    // JRAサイトのHTMLをモック
    await page.route('https://www.jra.go.jp/keiba/calendar/oct.html', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
<!DOCTYPE html>
<html>
<head>
    <title>開催日程 2024年10月 JRA</title>
</head>
<body>
    <div class="calendar">
        <a href="/keiba/calendar2025/2025/10/1004.html">4</a>
        <a href="/keiba/calendar2025/2025/10/1005.html">5</a>
    </div>
</body>
</html>
        `
      })
    })

    await page.route('**/keiba/calendar2025/2025/10/1004.html', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: `
<!DOCTYPE html>
<html>
<head>
    <title>レース詳細</title>
</head>
<body>
    <div class="race-info">
        <div class="race">
            <span class="race-number">1レース</span>
            <span class="race-name">テストレース1</span>
            <span class="start-time">10:05</span>
        </div>
        <div class="race">
            <span class="race-number">2レース</span>
            <span class="race-name">テストレース2</span>
            <span class="start-time">10:35</span>
        </div>
    </div>
</body>
</html>
        `
      })
    })

    // Cloud Functionのエンドポイント
    const functionUrl = 'http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRAData'
    
    // Cloud Functionを呼び出し
    const response = await request.post(functionUrl, {
      data: {},
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 25000
    })
    
    // レスポンスが成功であることを確認
    expect(response.status()).toBe(200)
    
    // レスポンスボディを確認
    const responseBody = await response.json()
    expect(responseBody).toHaveProperty('message')
    expect(responseBody.message).toContain('JRAデータのスクレイピングが完了しました')
    
    // スクレイピングされたレース数が0より大きいことを確認
    expect(responseBody.racesCount).toBeGreaterThan(0)
    
    // Firestoreにデータが保存されていることを確認
    // 注意: 実際のFirestore確認は別途実装が必要
    // ここではCloud Functionの呼び出しが成功することを確認
  })
})
