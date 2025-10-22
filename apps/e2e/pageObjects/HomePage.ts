import type { Page, Locator} from '@playwright/test'
import { expect } from '@playwright/test'
import { DashboardPage } from './DashboardPage'

export class HomePage {
  private page: Page

  constructor(page: Page) {
    this.page = page
    // ページが正しく読み込まれていることを検証
    expect(new globalThis.URL(page.url()).pathname).toBe('/')
  }

  // 静的メソッドでページ移動を簡潔に
  static async visit(page: Page): Promise<HomePage> {
    await page.goto('/', { timeout: 30000 }) // gotoは待機を含む
    return new HomePage(page)
  }

  // ページ要素
  private get title(): Locator {
    return this.page.locator('h1[aria-label="メインタイトル"]')
  }

  private get googleLoginButton(): Locator {
    return this.page.locator('button[aria-label="Googleでログイン"]')
  }

  private get loginModal(): Locator {
    return this.page.locator('.p-dialog')
  }

  private get loginModalGoogleButton(): Locator {
    return this.page.locator('button[aria-label="Googleでログイン"]')
  }

  private get emailInput(): Locator {
    return this.page.locator('input[aria-label="メールアドレス"]')
  }

  private get passwordInput(): Locator {
    return this.page.locator('input[aria-label="パスワード"]')
  }

  private get emailLoginButton(): Locator {
    return this.page.locator('button[aria-label="メールでログイン"]')
  }

  private get switchToEmailButton(): Locator {
    return this.page.locator('button[aria-label="メール認証に切り替え"]')
  }

  // 操作メソッド
  async clickGoogleLogin(): Promise<void> {
    // まずログインボタンをクリックしてダイアログを開く
    await this.page.locator('button:has-text("ログイン")').first().click()
    // ダイアログが表示されるまで待機
    await this.page.waitForSelector('.p-dialog')
    // Googleでログインボタンをクリック
    await this.googleLoginButton.click()
  }

  async loginWithGoogle(): Promise<DashboardPage> {
    // Googleログインはポップアップ形式のため、E2Eテストでは困難
    // 代わりにメール認証を使用
    return await this.loginWithEmailAndPassword('test@example.com', 'password123')
  }

  async loginWithEmailAndPassword(email: string, password: string): Promise<DashboardPage> {
    await this.page.locator('button[aria-label="ログインダイアログを開く"]').first().click({ timeout: 10000 })
    await this.page.waitForSelector('.p-dialog')
    await this.switchToEmailButton.click()
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    
    await this.emailLoginButton.click()
    await this.page.waitForURL(/\/dashboard$/, { timeout: 15000 })
    
    return new DashboardPage(this.page)
  }

  // データアクセスメソッド
  getGoogleLoginButton(): Locator {
    return this.googleLoginButton
  }

  getLoginModal(): Locator {
    return this.loginModal
  }

  // データアクセスメソッド
  async getTitleText(): Promise<string> {
    return await this.title.textContent() || ''
  }

}
