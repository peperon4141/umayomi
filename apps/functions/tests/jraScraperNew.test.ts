import { describe, test, expect, vi, beforeEach } from 'vitest'

// Playwrightのモック設定
const mockPage = {
  goto: vi.fn(),
  $$eval: vi.fn(),
  close: vi.fn()
}

const mockBrowser = {
  newContext: vi.fn().mockResolvedValue({
    newPage: vi.fn().mockResolvedValue(mockPage)
  }),
  close: vi.fn()
}

vi.mock('playwright', () => ({
  chromium: {
    launch: vi.fn().mockResolvedValue(mockBrowser)
  }
}))

// Firebase Functionsのモック
vi.mock('firebase-functions', () => ({
  logger: {
    info: vi.fn(),
    error: vi.fn()
  }
}))

import { scrapeJRAData } from '../src/scraper/jraScraper'

describe('JRA Scraper - New Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  test('JRA開催日程ページから個別開催日リンクを取得できる', async () => {
    // モックされたPlaywrightの関数を取得
    const { chromium } = await import('playwright')
    const mockBrowser = await chromium.launch()
    const mockContext = await mockBrowser.newContext()
    const mockPage = await mockContext.newPage()

    // ページのモック設定
    vi.mocked(mockPage.goto).mockResolvedValue(undefined)
    vi.mocked(mockPage.$$eval)
      .mockResolvedValueOnce([
        { href: '/keiba/calendar2025/2025/10/1012.html', text: '10月12日' },
        { href: '/keiba/calendar2025/2025/10/1013.html', text: '10月13日' },
        { href: '/keiba/calendar2025/2025/10/1014.html', text: '10月14日' }
      ])
      .mockResolvedValue([
        {
          raceNumber: '1',
          raceInfo: '2歳新馬 1,600m（芝）',
          startTime: '10:05',
          fullText: '1レース 2歳新馬 1,600m（芝） 10:05'
        },
        {
          raceNumber: '2',
          raceInfo: '2歳新馬 1,600m（ダート）',
          startTime: '10:35',
          fullText: '2レース 2歳新馬 1,600m（ダート） 10:35'
        },
        {
          raceNumber: '3',
          raceInfo: '2歳新馬 2,000m（芝）',
          startTime: '11:05',
          fullText: '3レース 2歳新馬 2,000m（芝） 11:05'
        }
      ])

    const result = await scrapeJRAData()

    expect(result).toBeDefined()
    expect(Array.isArray(result)).toBe(true)
    expect(result.length).toBeGreaterThan(0)

    // レース情報の検証
    const firstRace = result[0]
    expect(firstRace).toHaveProperty('raceName')
    expect(firstRace).toHaveProperty('racecourse')
    expect(firstRace).toHaveProperty('date')
    expect(firstRace).toHaveProperty('grade')
    expect(firstRace).toHaveProperty('surface')
    expect(firstRace).toHaveProperty('distance')
    expect(firstRace).toHaveProperty('startTime')
    expect(firstRace).toHaveProperty('source', 'JRA Race Day')
  })

  test('開催日程ページにアクセスできる', async () => {
    mockPage.goto.mockResolvedValue(undefined)
    mockPage.$$eval.mockResolvedValue([])

    await scrapeJRAData()

    expect(mockPage.goto).toHaveBeenCalledWith(
      'https://www.jra.go.jp/keiba/calendar/oct.html',
      { waitUntil: 'networkidle' }
    )
  })

  test('個別開催日ページにアクセスできる', async () => {
    const mockDayLinks = [
      { href: '/keiba/calendar2025/2025/10/1012.html', text: '10月12日' }
    ]

    mockPage.goto.mockResolvedValue(undefined)
    mockPage.$$eval
      .mockResolvedValueOnce(mockDayLinks)
      .mockResolvedValue([])

    await scrapeJRAData()

    expect(mockPage.goto).toHaveBeenCalledWith(
      'https://www.jra.go.jp/keiba/calendar/oct.html',
      { waitUntil: 'networkidle' }
    )
  })

  test('レース情報の解析が正しく動作する', async () => {
    const mockRaceData = [
      {
        raceNumber: '1',
        raceInfo: 'GⅠ 3歳以上 2,000m（芝）',
        startTime: '15:45',
        fullText: '1レース GⅠ 3歳以上 2,000m（芝） 15:45'
      }
    ]

    mockPage.goto.mockResolvedValue(undefined)
    mockPage.$$eval
      .mockResolvedValueOnce([{ href: '/test.html', text: 'テスト日' }])
      .mockResolvedValue(mockRaceData)

    const result = await scrapeJRAData()

    expect(result).toBeDefined()
    expect(result.length).toBe(1)
    
    const race = result[0]
    expect(race.raceName).toBe('GⅠ')
    expect(race.grade).toBe('GⅠ')
    expect(race.surface).toBe('芝')
    expect(race.distance).toBe(2000)
    expect(race.startTime).toBe('15:45')
  })

  test('エラーハンドリングが正しく動作する', async () => {
    mockPage.goto.mockRejectedValue(new Error('Network error'))

    await expect(scrapeJRAData()).rejects.toThrow('Network error')
  })

  test('ブラウザが正しくクローズされる', async () => {
    mockPage.goto.mockResolvedValue(undefined)
    mockPage.$$eval.mockResolvedValue([])

    await scrapeJRAData()

    expect(mockBrowser.close).toHaveBeenCalled()
  })

  test('レース情報のフィルタリングが正しく動作する', async () => {
    const mockRaceData = [
      {
        raceNumber: '1',
        raceInfo: '2歳新馬 1,600m（芝）',
        startTime: '10:05',
        fullText: '1レース 2歳新馬 1,600m（芝） 10:05'
      },
      {
        raceNumber: '',
        raceInfo: '',
        startTime: '',
        fullText: ''
      },
      {
        raceNumber: '2',
        raceInfo: '2歳新馬 1,600m（ダート）',
        startTime: '10:35',
        fullText: '2レース 2歳新馬 1,600m（ダート） 10:35'
      }
    ]

    mockPage.goto.mockResolvedValue(undefined)
    mockPage.$$eval
      .mockResolvedValueOnce([{ href: '/test.html', text: 'テスト日' }])
      .mockResolvedValue(mockRaceData)

    const result = await scrapeJRAData()

    expect(result).toBeDefined()
    expect(result.length).toBe(2) // 空のデータは除外される
  })
})
