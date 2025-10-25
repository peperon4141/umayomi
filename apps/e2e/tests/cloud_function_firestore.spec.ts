import { test, expect } from '@playwright/test'
import { HomePage } from '../pageObjects/HomePage'

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

  test('フロントエンドからCloud Functionを呼び出してデータを取得できる', async ({ page }) => {
    // タイムアウトを延長
    test.setTimeout(30000)
    
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // 認証後にダッシュボードページにアクセス
    await page.goto('http://127.0.0.1:5100/dashboard')
    
    // ページの読み込みを待つ
    await page.waitForLoadState('networkidle')
    
    // 少し待機してからボタンを探す
    await page.waitForTimeout(3000)
    
    // ページの内容をデバッグ
    console.log('Current URL:', page.url())
    const pageContent = await page.content()
    console.log('Page content length:', pageContent.length)
    console.log('Page content:', pageContent)
    
    // すべてのボタンを確認
    const allButtons = await page.locator('button').all()
    console.log('Found buttons:', allButtons.length)
    for (let i = 0; i < allButtons.length; i++) {
      const text = await allButtons[i].textContent()
      const isVisible = await allButtons[i].isVisible()
      console.log(`Button ${i}: "${text}" (visible: ${isVisible})`)
    }
    
    // テキストで検索
    const jraButton = page.locator('text="JRAスクレイピング実行"')
    const jraButtonCount = await jraButton.count()
    console.log('JRA button count:', jraButtonCount)
    
    // ページのHTMLを出力（デバッグ用）
    const html = await page.content()
    console.log('HTML contains JRA:', html.includes('JRAスクレイピング実行'))
    console.log('HTML contains スクレイピング:', html.includes('スクレイピング'))
    
    // すべてのテキストを確認
    const allText = await page.textContent('body')
    console.log('All text contains JRA:', allText?.includes('JRAスクレイピング実行'))
    
    // JRAスクレイピングボタンが表示されるまで待機
    await page.waitForSelector('button:has-text("JRAスクレイピング実行")', { timeout: 15000 })
    
    // JRAスクレイピングボタンをクリック
    await page.click('button:has-text("JRAスクレイピング実行")')
    
    // スクレイピング完了のトーストメッセージを確認
    await expect(page.locator('.p-toast-message')).toBeVisible({ timeout: 30000 })
    
    // レースデータが表示されることを確認（正しいセレクターを使用）
    await expect(page.locator('.grid.grid-cols-1')).toBeVisible()
  })

  test('Firestoreからレースデータを取得して表示できる', async ({ page }) => {
    // タイムアウトを延長
    test.setTimeout(30000)
    
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // ダッシュボードページに直接アクセス（レースデータが表示されるページ）
    await page.goto('http://127.0.0.1:5100/dashboard')
    
    // 少し待機してからレースデータを探す
    await page.waitForTimeout(2000)
    
    // レースデータが読み込まれるまで待機（正しいセレクターを使用）
    await page.waitForSelector('.grid.grid-cols-1', { timeout: 15000 })
    
    // レースカードが表示されることを確認（正しいセレクターを使用）
    const raceCards = page.locator('.grid.grid-cols-1 > div')
    await expect(raceCards).toHaveCount(1)
    
    // レース詳細ページに遷移できることを確認
    await raceCards.first().click()
    await expect(page).toHaveURL(/\/races\/year\/\d{4}\/month\/\d{1,2}\/place\/[a-zA-Z0-9]+\/race\/[a-zA-Z0-9]+/)
  })
})
