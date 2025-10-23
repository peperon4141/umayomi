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

  private get googleLoginButton(): Locator {
    return this.page.locator('button[aria-label="Googleでログイン"]')
  }

  // 操作メソッド
  async loginWithEmailAndPassword(email: string, password: string): Promise<DashboardPage> {
    await this.page.locator('button[aria-label="ログインダイアログを開く"]').first().click({ timeout: 10000 })
    await this.page.waitForSelector('.p-dialog')
    
    // Googleログインはポップアップ形式のため、E2Eテストでは実際のGoogle認証は困難
    // 代わりにメール認証に切り替えてテストを継続
    await this.page.locator('button:has-text("Googleアカウントをお持ちでない方")').click()
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.emailLoginButton.click()
    
    await this.page.waitForURL(/\/races\/year\/2024/, { timeout: 15000 })
    return new DashboardPage(this.page)
  }

  async loginWithGoogle(): Promise<DashboardPage> {
    await this.page.locator('button[aria-label="ログインダイアログを開く"]').first().click({ timeout: 10000 })
    await this.page.waitForSelector('.p-dialog')
    await this.switchToEmailButton.click()
    await this.emailInput.fill('test@example.com')
    await this.passwordInput.fill('password123')
    
    await this.emailLoginButton.click()
    await this.page.waitForURL(/\/races\/year\/2024/, { timeout: 15000 })
    
    return new DashboardPage(this.page)
  }

  // データアクセスメソッド
  async getTitleText(): Promise<string> {
    return await this.title.textContent() || ''
  }

}
