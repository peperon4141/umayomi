import type { Page, Locator} from '@playwright/test'
import { expect } from '@playwright/test'
import { RaceDetailPage } from './RaceDetailPage'

export class DashboardPage {
  private page: Page

  constructor(page: Page) {
    this.page = page
    // ページが正しく読み込まれていることを検証
    expect(new globalThis.URL(page.url()).pathname).toBe('/race-list')
  }

  // 静的メソッドでページ移動を簡潔に
  static async visit(page: Page): Promise<DashboardPage> {
    await page.goto('/race-list')
    return new DashboardPage(page)
  }

  // レース詳細ページに移動
  async goToRaceDetail(raceKey: string): Promise<RaceDetailPage> {
    // DataTableの行をクリック（race_keyに基づく）
    await this.page.click(`tr[data-race-key="${raceKey}"]`)
    await this.page.waitForURL(/\/race\/[a-zA-Z0-9_]+/)
    return new RaceDetailPage(this.page)
  }

  // レース一覧を取得（DataTableの行）
  getRaces(): Locator {
    return this.page.locator('tbody tr') // DataTableの行
  }

  // レース名で検索
  getRaceByTitle(title: string): Locator {
    return this.page.locator(`h3:has-text("${title}")`)
  }

  // レースなしメッセージを取得
  getNoRacesMessage(): Locator {
    return this.page.locator('[aria-label="レースなしメッセージ"]')
  }

  // ダッシュボードのタイトルを取得
  getTitle(): Locator {
    return this.page.locator('h1:has-text("レースリスト")')
  }

  // 競馬場フィルターを取得
  getRacecourseFilter(): Locator {
    return this.page.locator('text=競馬場を選択')
  }

  // フィルターリセットボタンをクリック
  async clickResetFilter(): Promise<void> {
    await this.page.locator('button:has-text("フィルターリセット")').click()
  }

  // ログアウト処理
  async logout(): Promise<void> {
    // ユーザーメニューをクリック
    await this.page.locator('[aria-label="ユーザーメニュー"]').click()
    // ログアウトボタンをクリック
    await this.page.locator('[aria-label="ログアウト"]').click()
  }
}
