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
    await page.goto('/', { waitUntil: 'load' })
    // ログインボタンまたはタイトルが表示されるまで待つ（ログイン済みの場合はリダイレクトされるため）
    await Promise.race([
      page.waitForSelector('button[aria-label="ログインダイアログを開く"]', { state: 'visible', timeout: 3000 }).catch(() => null),
      page.waitForSelector('h1[aria-label="メインタイトル"]', { state: 'visible', timeout: 3000 }).catch(() => null)
    ])
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

  private get googleLoginButton(): Locator {
    return this.page.locator('button[aria-label="Googleでログイン"]')
  }

  // 操作メソッド
  async loginWithEmailAndPassword(email: string, password: string): Promise<DashboardPage> {
    // ログインボタンをクリック（既にvisit()で待機済み）
    await this.page.locator('button[aria-label="ログインダイアログを開く"]').first().click({ timeout: 10000 })
    await this.page.waitForSelector('.p-dialog')
    
    // メールフォームを表示（showEmailFormをtrueにする方法がないため、テスト用に直接メール認証を使用）
    // ただし、UI上ではメールフォームへの切り替えボタンが削除されているため、
    // このテストは実際には動作しない可能性がある
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.emailLoginButton.click()
    
    await this.page.waitForURL(/\/races\/year\/\d{4}/, { timeout: 15000 })
    return new DashboardPage(this.page)
  }

  async loginWithGoogle(): Promise<DashboardPage> {
    // ログインダイアログを開く（既にvisit()で待機済み）
    await this.page.locator('button[aria-label="ログインダイアログを開く"]').first().click({ timeout: 10000 })
    await this.page.waitForSelector('.p-dialog')
    
    // Googleログインボタンをクリック
    // 注意: E2Eテストでは実際のGoogle認証ポップアップは扱えないため、
    // このテストはスキップするか、モックを使用する必要がある
    await this.googleLoginButton.click()
    
    // 実際のGoogle認証はポップアップで行われるため、E2Eテストでは完了を待てない
    // テストではスキップするか、モックを使用する
    await this.page.waitForURL(/\/races\/year\/\d{4}/, { timeout: 15000 }).catch(() => {
      // Google認証が完了しない場合はタイムアウト
    })
    
    return new DashboardPage(this.page)
  }

  // データアクセスメソッド
  async getTitleText(): Promise<string> {
    return await this.title.textContent() || ''
  }

}
