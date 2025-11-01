import { test, expect } from '@playwright/test'
import { HomePage } from '../pageObjects/HomePage'
import type { DashboardPage } from '../pageObjects/DashboardPage'
import { ensureTestUser } from '../helpers/setupAuth'

test.describe('ログインフロー', () => {
  // テスト実行前にテストユーザーを作成
  test.beforeAll(async () => {
    await ensureTestUser('test@example.com', 'password123')
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
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // レース一覧ページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('Googleログインでログインしたらレースページに自動遷移する', async ({ page }) => {
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // Googleログインでログイン
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // レース一覧ページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('メール認証でログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // ページをリロード
    await page.reload()
    
    // リロード後も同じページにいることを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // ダッシュボードページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('Googleログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // ページをリロード
    await page.reload()
    
    // リロード後も同じページにいることを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    // ダッシュボードページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('メール認証でログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    const dashboardPage: DashboardPage = await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // ログアウト
    await dashboardPage.logout()
    
    // ホームページに遷移することを確認
    await expect(page).toHaveURL('/')
    
    // 管理画面にアクセスしようとする
    await page.goto('/admin')
    
    // ホームページにリダイレクトされることを確認
    await expect(page).toHaveURL('/')
  })

  test('Googleログインでログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    const dashboardPage: DashboardPage = await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // ログアウト
    await dashboardPage.logout()
    
    // ホームページに遷移することを確認
    await expect(page).toHaveURL('/')
    
    // 管理画面にアクセスしようとする
    await page.goto('/admin')
    
    // ホームページにリダイレクトされることを確認
    await expect(page).toHaveURL('/')
  })

  test('メール認証でAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await expect(page.locator('h1:has-text("管理ダッシュボード")')).toBeVisible()
  })

  test('GoogleログインでAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/\d{4}/)
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await expect(page.locator('h1:has-text("管理ダッシュボード")')).toBeVisible()
  })
})
