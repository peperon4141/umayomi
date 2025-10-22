import { scrapeJRAData } from '../src/index'

// モック用のRequest/Response型
interface MockRequest {
  method: string
  url: string
  body: any
  query: any
  headers: any
  get: jest.Mock
}

interface MockResponse {
  send: jest.Mock
  status: jest.Mock
}

// Playwrightのモック
jest.mock('playwright', () => ({
  chromium: {
    launch: jest.fn().mockResolvedValue({
      newContext: jest.fn().mockResolvedValue({
        newPage: jest.fn().mockResolvedValue({
          goto: jest.fn(),
          $$eval: jest.fn(),
          evaluate: jest.fn(),
          close: jest.fn()
        })
      }),
      close: jest.fn()
    })
  }
}))

// Firebase Admin SDKのモック
jest.mock('firebase-admin/app', () => ({
  initializeApp: jest.fn()
}))

jest.mock('firebase-admin/firestore', () => ({
  getFirestore: jest.fn().mockReturnValue({
    batch: jest.fn().mockReturnValue({
      set: jest.fn(),
      commit: jest.fn().mockResolvedValue(undefined)
    }),
    collection: jest.fn().mockReturnValue({
      doc: jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue({
          exists: false
        })
      })
    })
  }),
  Timestamp: {
    fromDate: jest.fn().mockReturnValue('mock-timestamp'),
    now: jest.fn().mockReturnValue('mock-now-timestamp')
  }
}))

describe('JRA Scraper Function', () => {
  let req: MockRequest
  let res: MockResponse

  beforeEach(() => {
    req = {
      body: {},
      query: {},
      headers: {},
      method: 'POST',
      url: '',
      get: jest.fn(),
    }

    res = {
      send: jest.fn(),
      status: jest.fn().mockReturnThis(),
    }
  })

  it('should return success message when scraping completes', async () => {
    // モックデータを設定
    const mockPage = {
      goto: jest.fn().mockResolvedValue(undefined),
      $$eval: jest.fn().mockResolvedValue([
        { href: '/result/20251005/tokyo/1/', text: '東京1R' }
      ]),
      evaluate: jest.fn().mockResolvedValue({
        date: '2025年10月5日',
        racecourse: '東京',
        raceNumber: 1,
        raceName: '新馬戦',
        grade: '新馬',
        surface: '芝',
        distance: 1600,
        weather: '晴',
        trackCondition: '良',
        results: [
          { rank: 1, horseName: 'サンプルホース1', jockey: '騎手A', odds: 2.5 },
          { rank: 2, horseName: 'サンプルホース2', jockey: '騎手B', odds: 3.2 }
        ]
      }),
      close: jest.fn()
    }

    const mockBrowser = {
      newContext: jest.fn().mockResolvedValue({
        newPage: jest.fn().mockResolvedValue(mockPage)
      }),
      close: jest.fn()
    }

    const { chromium } = require('playwright')
    chromium.launch.mockResolvedValue(mockBrowser)

    await scrapeJRAData(req as any, res as any)

    expect(res.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: 'JRAデータのスクレイピングが完了しました',
        racesCount: expect.any(Number)
      })
    )
  })

  it('should handle network errors gracefully', async () => {
    const mockPage = {
      goto: jest.fn().mockRejectedValue(new Error('Network error')),
      close: jest.fn()
    }

    const mockBrowser = {
      newContext: jest.fn().mockResolvedValue({
        newPage: jest.fn().mockResolvedValue(mockPage)
      }),
      close: jest.fn()
    }

    const { chromium } = require('playwright')
    chromium.launch.mockResolvedValue(mockBrowser)

    await scrapeJRAData(req as any, res as any)

    expect(res.status).toHaveBeenCalledWith(500)
    expect(res.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: false,
        error: expect.stringContaining('Network error')
      })
    )
  })

  it('should parse race results correctly', async () => {
    const mockRaceData = {
      date: '2025年10月5日',
      racecourse: '東京',
      raceNumber: 1,
      raceName: '新馬戦',
      grade: '新馬',
      surface: '芝',
      distance: 1600,
      weather: '晴',
      trackCondition: '良',
      results: [
        { rank: 1, horseName: 'サンプルホース1', jockey: '騎手A', odds: 2.5 },
        { rank: 2, horseName: 'サンプルホース2', jockey: '騎手B', odds: 3.2 }
      ]
    }

    const mockPage = {
      goto: jest.fn().mockResolvedValue(undefined),
      $$eval: jest.fn().mockResolvedValue([
        { href: '/result/20251005/tokyo/1/', text: '東京1R' }
      ]),
      evaluate: jest.fn().mockResolvedValue(mockRaceData),
      close: jest.fn()
    }

    const mockBrowser = {
      newContext: jest.fn().mockResolvedValue({
        newPage: jest.fn().mockResolvedValue(mockPage)
      }),
      close: jest.fn()
    }

    const { chromium } = require('playwright')
    chromium.launch.mockResolvedValue(mockBrowser)

    await scrapeJRAData(req as any, res as any)

    expect(res.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        races: expect.arrayContaining([
          expect.objectContaining({
            racecourse: '東京',
            raceNumber: 1,
            raceName: '新馬戦',
            results: expect.arrayContaining([
              expect.objectContaining({
                rank: 1,
                horseName: 'サンプルホース1',
                jockey: '騎手A',
                odds: 2.5
              })
            ])
          })
        ])
      })
    )
  })

  it('should handle empty race results', async () => {
    const mockPage = {
      goto: jest.fn().mockResolvedValue(undefined),
      $$eval: jest.fn().mockResolvedValue([]), // 空のレース結果
      close: jest.fn()
    }

    const mockBrowser = {
      newContext: jest.fn().mockResolvedValue({
        newPage: jest.fn().mockResolvedValue(mockPage)
      }),
      close: jest.fn()
    }

    const { chromium } = require('playwright')
    chromium.launch.mockResolvedValue(mockBrowser)

    await scrapeJRAData(req as any, res as any)

    expect(res.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: 'JRAデータのスクレイピングが完了しました',
        racesCount: 0
      })
    )
  })

  it('should save races to Firestore', async () => {
    const mockPage = {
      goto: jest.fn().mockResolvedValue(undefined),
      $$eval: jest.fn().mockResolvedValue([
        { href: '/result/20251005/tokyo/1/', text: '東京1R' }
      ]),
      evaluate: jest.fn().mockResolvedValue({
        date: '2025年10月5日',
        racecourse: '東京',
        raceNumber: 1,
        raceName: '新馬戦',
        grade: '新馬',
        surface: '芝',
        distance: 1600,
        weather: '晴',
        trackCondition: '良',
        results: [
          { rank: 1, horseName: 'サンプルホース1', jockey: '騎手A', odds: 2.5 }
        ]
      }),
      close: jest.fn()
    }

    const mockBrowser = {
      newContext: jest.fn().mockResolvedValue({
        newPage: jest.fn().mockResolvedValue(mockPage)
      }),
      close: jest.fn()
    }

    const { chromium } = require('playwright')
    chromium.launch.mockResolvedValue(mockBrowser)

    await scrapeJRAData(req as any, res as any)

    expect(res.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: 'JRAデータのスクレイピングが完了しました',
        racesCount: expect.any(Number),
        savedCount: expect.any(Number)
      })
    )
  })
})
