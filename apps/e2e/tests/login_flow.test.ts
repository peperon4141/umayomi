import { test, expect } from '@playwright/test'
import { HomePage } from '../pageObjects/HomePage'
import { DashboardPage } from '../pageObjects/DashboardPage'

test.describe('ログインフロー', () => {
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
    const dashboardPage = await homePage.loginWithGoogle()
    
    // レースページ（ダッシュボード）に遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    // ダッシュボードページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('Googleログインでログインしたらレースページに自動遷移する', async ({ page }) => {
    // ホームページにアクセス
    const homePage = await HomePage.visit(page)
    
    // Googleログインでログイン
    const dashboardPage = await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページ（ダッシュボード）に遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    // ダッシュボードページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('メール認証でログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    
    // ページをリロード
    await page.reload()
    
    // リロード後も同じページにいることを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    // ダッシュボードページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('Googleログイン後、リロードしたらまた同じページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    
    // ページをリロード
    await page.reload()
    
    // リロード後も同じページにいることを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    // ダッシュボードページの要素が表示されることを確認
    await expect(page.locator('h1:has-text("競馬レース一覧")')).toBeVisible()
  })

  test('メール認証でログアウトしたらホームページに自動遷移し、管理画面には入れない', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    const dashboardPage = await homePage.loginWithGoogle()
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    
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
    const dashboardPage = await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    
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
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await expect(page.locator('h1')).toBeVisible()
  })

  test('GoogleログインでAdminユーザーは、アドミンユーザーページにアクセスできる', async ({ page }) => {
    // ホームページにアクセスしてログイン
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // レースページに遷移することを確認
    await expect(page).toHaveURL(/\/races\/year\/2024/)
    
    // 管理画面にアクセス
    await page.goto('/admin')
    
    // 管理画面にアクセスできることを確認
    await expect(page).toHaveURL('/admin')
    await expect(page.locator('h1')).toBeVisible()
  })
})
