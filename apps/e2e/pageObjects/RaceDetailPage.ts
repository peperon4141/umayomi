import type { Page, Locator} from '@playwright/test'
import { expect } from '@playwright/test'

export class RaceDetailPage {
  private page: Page

  constructor(page: Page) {
    this.page = page
    // ページが正しく読み込まれていることを検証
    expect(new globalThis.URL(page.url()).pathname).toMatch(/\/race\/[a-zA-Z0-9]+/)
  }

  // 静的メソッドでページ移動を簡潔に
  static async visit(page: Page, raceId: string): Promise<RaceDetailPage> {
    await page.goto(`/race/${raceId}`)
    return new RaceDetailPage(page)
  }

  // レース名を取得
  getRaceName(): Locator {
    return this.page.locator('h1')
  }

  // レース情報を取得
  getRaceInfo(): Locator {
    return this.page.locator('.race-info')
  }

  // レース結果テーブルを取得
  getRaceResultsTable(): Locator {
    return this.page.locator('.race-results-table')
  }

  // 着順を取得
  getRankings(): Locator {
    return this.page.locator('td[data-field="rank"]')
  }

  // 馬名を取得
  getHorseNames(): Locator {
    return this.page.locator('td[data-field="horseName"]')
  }

  // 騎手名を取得
  getJockeys(): Locator {
    return this.page.locator('td[data-field="jockey"]')
  }

  // タイムを取得
  getTimes(): Locator {
    return this.page.locator('td[data-field="time"]')
  }

  // オッズを取得
  getOdds(): Locator {
    return this.page.locator('td[data-field="odds"]')
  }

  // パンくずリストを取得
  getBreadcrumb(): Locator {
    return this.page.locator('.p-breadcrumb')
  }

  // ホームに戻る
  async goHome(): Promise<void> {
    await this.page.locator('a:has-text("ホーム")').click()
    await this.page.waitForURL('/')
  }

  // ダッシュボードに戻る
  async goToDashboard(): Promise<void> {
    await this.page.locator('a:has-text("ダッシュボード")').click()
    await this.page.waitForURL('/dashboard')
  }
}
