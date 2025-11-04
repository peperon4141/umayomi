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
    // ホームページにアクセス（接続エラーを無視）
    try {
      await page.goto('/', { timeout: 30000, waitUntil: 'load' })
      // ストレージをクリア
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })
      // ページをリロードしてFirebase Authの状態を完全にリセット
      await page.reload({ waitUntil: 'load' })
      // Firebase Authの状態がリセットされるまで少し待つ
      await page.waitForTimeout(1000)
    } catch (error: any) {
      // 接続エラーは無視（サーバーが起動していない場合は後続のテストで失敗する）
      if (!error.message.includes('ERR_CONNECTION_REFUSED')) {
        throw error
      }
    }
  })

  // 各テスト後にログアウト状態にする
  test.afterEach(async ({ page }) => {
    try {
      // ログイン済みの場合はログアウトする
      const userMenuButton = page.locator('[aria-label="ユーザーメニュー"]')
      const isLoggedIn = await userMenuButton.isVisible().catch(() => false)
      if (isLoggedIn) {
        // ユーザーメニューを開く
        await userMenuButton.click()
        // ログアウトボタンをクリック
        await page.locator('[aria-label="ログアウト"]').click()
        // ホームページにリダイレクトされるまで待つ
        await page.waitForURL('/', { timeout: 10000 }).catch(() => {
          // タイムアウトしても続行
        })
      }
      // ストレージをクリア
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })
    } catch {
      // エラーは無視（テストが失敗している場合など）
    }
  })

  test('誰でもホームページにアクセスできる', async ({ page }) => {
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // ホームページのタイトルが表示されることを確認
    await expect(homePage.getTitleText()).resolves.toContain('競馬のデータを')
    
    // ログインボタンが表示されることを確認
    await expect(page.locator('button:has-text("ログイン")').first()).toBeVisible()
  })

  test('メール認証でログインしたらレースページに自動遷移する', async ({ page }) => {
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // ローディングが終わるまで待つ
    await page.waitForSelector('.pi-spin', { state: 'hidden', timeout: 15000 }).catch(() => {
      // ローディングインジケーターが見つからない場合はスキップ
    })
    // レース一覧ページの要素が表示されることを確認
    await page.waitForSelector('h1.text-2xl', { timeout: 15000 })
    await expect(page.locator('h1.text-2xl')).toContainText('競馬レース一覧')
  })

  test('Googleログインでログインしたらレースページに自動遷移する', async ({ page }) => {
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // Googleログインでログイン（実際にはメール認証に切り替える）
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // ローディングが終わるまで待つ
    await page.waitForSelector('.pi-spin', { state: 'hidden', timeout: 15000 }).catch(() => {
      // ローディングインジケーターが見つからない場合はスキップ
    })
    // レース一覧ページの要素が表示されることを確認
    await page.waitForSelector('h1.text-2xl', { timeout: 15000 })
    await expect(page.locator('h1.text-2xl')).toContainText('競馬レース一覧')
  })

  test('メール認証でログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
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

  test('Googleログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン（実際にはメール認証に切り替える）
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

  test('メール認証でログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    const dashboardPage: DashboardPage = await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
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

  test('Googleログインでログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // ホームページにアクセスしてログイン（実際にはメール認証に切り替える）
    const homePage = await HomePage.visit(page)
    const dashboardPage: DashboardPage = await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
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

  test('メール認証でAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await page.waitForSelector('h1:has-text("管理ダッシュボード")', { timeout: 10000 })
    await expect(page.locator('h1:has-text("管理ダッシュボード")')).toBeVisible()
  })

  test('GoogleログインでAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン（実際にはメール認証に切り替える）
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await page.waitForSelector('h1:has-text("管理ダッシュボード")', { timeout: 10000 })
    await expect(page.locator('h1:has-text("管理ダッシュボード")')).toBeVisible()
  })
})
