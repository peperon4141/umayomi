import type { Page, Locator} from '@playwright/test'
import { expect } from '@playwright/test'
import { RaceDetailPage } from './RaceDetailPage'

export class DashboardPage {
  private page: Page

  constructor(page: Page) {
    this.page = page
    // ページが正しく読み込まれていることを検証
    expect(new globalThis.URL(page.url()).pathname).toBe('/dashboard')
  }

  // 静的メソッドでページ移動を簡潔に
  static async visit(page: Page): Promise<DashboardPage> {
    await page.goto('/dashboard')
    return new DashboardPage(page)
  }

  // レース詳細ページに移動
  async goToRaceDetail(raceId: string): Promise<RaceDetailPage> {
    await this.page.click(`[data-race-id="${raceId}"]`)
    await this.page.waitForURL(/\/race\/[a-zA-Z0-9]+/)
    return new RaceDetailPage(this.page)
  }

  // レース一覧を取得
  getRaces(): Locator {
    return this.page.locator('.races-grid > div') // レースカードのコンテナ
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
    return this.page.locator('h1:has-text("競馬レース結果")')
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
