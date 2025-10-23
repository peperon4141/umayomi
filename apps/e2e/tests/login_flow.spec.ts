import { test, expect } from '@playwright/test'
import { HomePage } from '../pageObjects/HomePage'
import { DashboardPage } from '../pageObjects/DashboardPage'

test.describe('ログインフロー', () => {
  test('ユーザーが、ホームページにアクセスできる', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    await expect(page).toHaveTitle(/馬予想/) // ページタイトルを確認
    await expect(homePage.getTitleText()).resolves.toContain('競馬') // メインタイトルが表示されることを確認
    
    // ログインボタンをクリックしてダイアログを開く
    await page.click('button:has-text("ログイン")')
    await page.waitForTimeout(1000) // モーダル表示の待機
    await expect(homePage.getLoginModal()).toBeVisible() // ログインモーダルが表示されることを確認
  })

  test('ユーザーが、ログインモーダルが表示される', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    // Googleログインボタンをクリック
    await homePage.clickGoogleLogin()
    await page.waitForTimeout(1000) // モーダル表示の待機
    
    // ログインモーダルが表示されることを確認
    await expect(homePage.getLoginModal()).toBeVisible()
    
    // モーダルが表示されたことを確認（ログイン機能は未実装のため、ここでテスト終了）
  })

  test('Firebase Emulatorでメール認証ができる', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページにリダイレクトされることを確認
    await expect(page).toHaveURL('/races/year/2024')
    
    // ダッシュボードの要素が表示されることを確認
    const dashboardPage = new DashboardPage(page)
    await expect(dashboardPage.getTitle()).toBeVisible()
  })

  test('ログイン後、ダッシュボードにアクセスできる', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページにリダイレクトされることを確認
    await expect(page).toHaveURL('/races/year/2024')
    
    // ダッシュボードの要素が表示されることを確認
    const dashboardPage = new DashboardPage(page)
    await expect(dashboardPage.getTitle()).toBeVisible()
  })

  test('未認証ユーザーはダッシュボードにアクセスできない', async ({ page }) => {
    // 未認証状態でダッシュボードに直接アクセス
    await page.goto('/dashboard')
    
    // ホームページにリダイレクトされることを確認
    await expect(page).toHaveURL('/')
    
    // ホームページの要素が表示されることを確認
    const homePage = new HomePage(page)
    // ログインボタンをクリックしてダイアログを開く
    await page.click('button:has-text("ログイン")')
    await expect(homePage.getGoogleLoginButton()).toBeVisible()
  })

  test('ログアウト後、ホームページにリダイレクトされる', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページにリダイレクトされることを確認
    await expect(page).toHaveURL('/races/year/2024')
    
    // ログアウト処理
    const dashboardPage = new DashboardPage(page)
    await dashboardPage.logout()
    
    // ホームページにリダイレクトされることを確認
    await expect(page).toHaveURL('/')
    
    // ホームページの要素が表示されることを確認
    const loggedOutHomePage = new HomePage(page)
    // ログインボタンをクリックしてダイアログを開く
    await page.click('button:has-text("ログイン")')
    await expect(loggedOutHomePage.getGoogleLoginButton()).toBeVisible()
  })

  test('ログイン後、ページリロードしても認証状態が維持される', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページにリダイレクトされることを確認
    await expect(page).toHaveURL('/races/year/2024')
    
    // ダッシュボードの要素が表示されることを確認
    const dashboardPage = new DashboardPage(page)
    await expect(dashboardPage.getTitle()).toBeVisible()
    
    // ユーザーメニューが表示されることを確認
    await expect(page.locator('button[aria-label="ユーザーメニュー"]')).toBeVisible()
    
    // 認証状態が確実に設定されるまで少し待機
    await page.waitForTimeout(1000)
    
    // ページをリロード
    await page.reload()
    
    // リロード後、ダッシュボードの要素が表示されるまで待機
    await expect(page).toHaveURL('/dashboard')
    await expect(dashboardPage.getTitle()).toBeVisible()
    
    // ユーザーメニューが表示されることを確認（認証状態が維持されている）
    await expect(page.locator('button[aria-label="ユーザーメニュー"]')).toBeVisible()
  })

  test('認証済みユーザーがホームページにアクセスするとダッシュボードにリダイレクトされる', async ({ page }) => {
    // ホームページに移動
    const homePage = await HomePage.visit(page)
    
    // メール認証でログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページにリダイレクトされることを確認
    await expect(page).toHaveURL('/races/year/2024')
    
    // ホームページに直接アクセス
    await page.goto('/')
    
    // レースページにリダイレクトされることを確認
    await expect(page).toHaveURL('/races/year/2024')
  })
})
