import { test, expect } from '@playwright/test'
import { HomePage } from '../pageObjects/HomePage'

test.describe('競馬レース結果ダッシュボード', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to dashboard - will redirect to login if not authenticated
    await page.goto('/dashboard')
  })

  test('未認証ユーザーはホームページにリダイレクトされる', async ({ page }) => {
    // Should redirect to home page when not authenticated
    await expect(page).toHaveURL('/')
  })

  test('リダイレクト時にホームページが表示される', async ({ page }) => {
    await expect(page.locator('h1[aria-label="メインタイトル"]')).toContainText('競馬')
    await expect(page.locator('button:has-text("ログイン")').first()).toBeVisible()
  })

  test('認証済みユーザーはダッシュボードにアクセスできる', async ({ page }) => {
    // Login first
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Dashboard should be visible
    await expect(page.locator('text=競馬レース結果')).toBeVisible()
  })

  test('レース結果が表示される', async ({ page }) => {
    // Login first
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Dashboard should show race results
    await expect(page.locator('text=競馬レース結果')).toBeVisible()
    await expect(page.locator('text=2025年10月分のレース結果を表示しています')).toBeVisible()
  })

  test('競馬場フィルターが機能する', async ({ page }) => {
    // Login first
    const homePage = await HomePage.visit(page)
    await homePage.loginWithGoogle()
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Check if racecourse filter is present
    await expect(page.locator('text=競馬場を選択')).toBeVisible()
  })

  test('メール認証でログイン後、ダッシュボードにアクセスできる', async ({ page }) => {
    // Login with email and password
    const homePage = await HomePage.visit(page)
    await homePage.loginWithEmailAndPassword('test@example.com', 'password123')
    
    // Should be redirected to dashboard
    await expect(page).toHaveURL('/dashboard')
    
    // Dashboard should be visible
    await expect(page.locator('text=競馬レース結果')).toBeVisible()
  })
})
