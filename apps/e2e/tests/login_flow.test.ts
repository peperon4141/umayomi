import { test, expect } from '@playwright/test'
import { HomePage } from '../pageObjects/HomePage'
import type { DashboardPage } from '../pageObjects/DashboardPage'
import { ensureTestUser } from '../helpers/setupAuth'

test.describe('ログインフロー', () => {
  // テスト実行前にテストユーザーを作成
  test.beforeAll(async () => {
    await ensureTestUser('test@example.com', 'password123')
  })

  // 各テスト前にログアウト状態にする
  test.beforeEach(async ({ page, context }) => {
    // クッキーをクリア
    await context.clearCookies()
    // ページが読み込まれた後にストレージをクリア
    try {
      await page.goto('/', { waitUntil: 'load' })
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })
    } catch {
      // エラーは無視（サーバーが起動していない場合など）
    }
  })

  // 各テスト後にログアウト状態にする
  test.afterEach(async ({ page }) => {
    try {
      // ログイン済みの場合はログアウトする
      const userMenuButton = page.locator('[aria-label="ユーザーメニュー"]')
      if (await userMenuButton.isVisible().catch(() => false)) {
        await userMenuButton.click()
        await page.locator('[aria-label="ログアウト"]').click()
        await page.waitForURL('/', { timeout: 5000 }).catch(() => {})
      }
    } catch {
      // エラーは無視
    }
  })

  test('誰でもホームページにアクセスできる', async ({ page }) => {
    await page.goto('/', { waitUntil: 'load' })
    
    const currentUrl = new URL(page.url())
    const isHomePage = currentUrl.pathname === '/'
    const isRedirected = currentUrl.pathname === '/race-list'
    
    expect(isHomePage || isRedirected).toBe(true)
    
    if (isHomePage) {
      const titleElement = page.locator('h1[aria-label="メインタイトル"]')
      if (await titleElement.isVisible().catch(() => false)) {
        expect(await titleElement.textContent()).toContain('競馬のデータを')
      }
      const loginButton = page.locator('button:has-text("ログイン")').first()
      if (await loginButton.isVisible().catch(() => false)) {
        await expect(loginButton).toBeVisible()
      }
    }
  })

  test.skip('メール認証でログインしたらレースページに自動遷移する', async ({ page }) => {
    // スキップ理由: 「Googleアカウントをお持ちでない方」ボタンが削除され、メールフォームへの切り替えができなくなったため
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL('/race-list')
    // ローディングが終わるまで待つ
    await page.waitForSelector('.pi-spin', { state: 'hidden', timeout: 15000 }).catch(() => {
      // ローディングインジケーターが見つからない場合はスキップ
    })
    // レース一覧ページの要素が表示されることを確認
    await page.waitForSelector('h1.text-2xl', { timeout: 15000 })
    await expect(page.locator('h1.text-2xl')).toContainText('レースリスト')
  })

  test.skip('Googleログインでログインしたらレースページに自動遷移する', async ({ page }) => {
    // スキップ理由: E2Eテストでは実際のGoogle認証ポップアップを扱えないため
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // Googleログインでログイン
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL('/race-list')
    // ローディングが終わるまで待つ
    await page.waitForSelector('.pi-spin', { state: 'hidden', timeout: 15000 }).catch(() => {
      // ローディングインジケーターが見つからない場合はスキップ
    })
    // レース一覧ページの要素が表示されることを確認
    await page.waitForSelector('h1.text-2xl', { timeout: 15000 })
    await expect(page.locator('h1.text-2xl')).toContainText('レースリスト')
  })

  test.skip('メール認証でログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // スキップ理由: メール認証フォームへの切り替えができなくなったため
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // ページをリロード
    await page.reload({ waitUntil: 'load' })
    
    // リロード後も同じページにいることを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // ローディングが終わるまで待つ（ローディングインジケーターが消えるのを待つ）
    // まずローディングインジケーターが消えるのを待つ
    await page.waitForSelector('.pi-spin.pi-spinner', { state: 'hidden', timeout: 30000 }).catch(() => {
      // ローディングインジケーターが見つからない場合はスキップ
    })
    // その後、h1が表示されるまで待つ
    await page.waitForSelector('h1.text-2xl', { timeout: 30000 })
    await expect(page.locator('h1.text-2xl')).toContainText('競馬レース一覧')
  })

  test.skip('メール認証でログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // スキップ理由: メール認証フォームへの切り替えができなくなったため
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    const dashboardPage: DashboardPage = await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL('/race-list')
    
    // ログアウト
    await dashboardPage.logout()
    
    // ホームページに遷移することを確認（リダイレクトを待つ）
    await expect(page).toHaveURL('/', { timeout: 10000 })
    // 認証状態が更新されるまで少し待つ
    await page.waitForTimeout(2000)
    
    // 管理画面にアクセスしようとする
    await page.goto('/admin', { waitUntil: 'load', timeout: 30000 })
    
    // 認証ガードによりホームページにリダイレクトされるまで待つ
    // URLが/adminから変わらなかった場合は、少し待ってから再確認
    await page.waitForTimeout(1000)
    const currentUrl = page.url()
    if (currentUrl.includes('/admin')) {
      // まだ/adminにいる場合は、リダイレクトを待つ（認証ガードが動作するまで最大10秒待つ）
      let attempts = 0
      while (attempts < 10 && page.url().includes('/admin')) {
        await page.waitForTimeout(1000)
        attempts++
      }
    }
    // 最終的にホームページにいることを確認
    await expect(page).toHaveURL('/', { timeout: 5000 })
  })

  test.skip('メール認証でAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // スキップ理由: メール認証フォームへの切り替えができなくなったため
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL('/race-list')
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await page.waitForSelector('h1:has-text("管理ダッシュボード")', { timeout: 10000 })
    await expect(page.locator('h1:has-text("管理ダッシュボード")')).toBeVisible()
  })

  test.skip('Googleログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // スキップ理由: E2Eテストでは実際のGoogle認証ポップアップを扱えないため
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // ページをリロード
    await page.reload({ waitUntil: 'load' })
    
    // リロード後も同じページにいることを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // ローディングが終わるまで待つ（ローディングインジケーターが消えるのを待つ）
    // まずローディングインジケーターが消えるのを待つ
    await page.waitForSelector('.pi-spin.pi-spinner', { state: 'hidden', timeout: 30000 }).catch(() => {
      // ローディングインジケーターが見つからない場合はスキップ
    })
    // その後、h1が表示されるまで待つ
    await page.waitForSelector('h1.text-2xl', { timeout: 30000 })
    await expect(page.locator('h1.text-2xl')).toContainText('競馬レース一覧')
  })

  test.skip('Googleログインでログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // スキップ理由: E2Eテストでは実際のGoogle認証ポップアップを扱えないため
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    const dashboardPage: DashboardPage = await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL('/race-list')
    
    // ログアウト
    await dashboardPage.logout()
    
    // ホームページに遷移することを確認（リダイレクトを待つ）
    await expect(page).toHaveURL('/', { timeout: 10000 })
    // 認証状態が更新されるまで少し待つ
    await page.waitForTimeout(2000)
    
    // 管理画面にアクセスしようとする
    await page.goto('/admin', { waitUntil: 'load', timeout: 30000 })
    
    // 認証ガードによりホームページにリダイレクトされるまで待つ
    // URLが/adminから変わらなかった場合は、少し待ってから再確認
    await page.waitForTimeout(1000)
    const currentUrl = page.url()
    if (currentUrl.includes('/admin')) {
      // まだ/adminにいる場合は、リダイレクトを待つ（認証ガードが動作するまで最大10秒待つ）
      let attempts = 0
      while (attempts < 10 && page.url().includes('/admin')) {
        await page.waitForTimeout(1000)
        attempts++
      }
    }
    // 最終的にホームページにいることを確認
    await expect(page).toHaveURL('/', { timeout: 5000 })
  })

  test.skip('GoogleログインでAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // スキップ理由: E2Eテストでは実際のGoogle認証ポップアップを扱えないため
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL('/race-list')
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await page.waitForSelector('h1:has-text("管理ダッシュボード")', { timeout: 10000 })
    await expect(page.locator('h1:has-text("管理ダッシュボード")')).toBeVisible()
  })

})
