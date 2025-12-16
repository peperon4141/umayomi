import { describe, it, expect, afterAll, vi, beforeEach } from 'vitest'
import firebaseFunctionsTest from 'firebase-functions-test'
import { readFileSync } from 'fs'
import { join } from 'path'

// モックをファイルの先頭で定義
vi.mock('../../src/utils/htmlFetcher', () => ({
  fetchJRAHtmlWithPlaywright: vi.fn()
}))

vi.mock('../../src/utils/firestoreSaver', () => ({
  saveRacesToFirestore: vi.fn()
}))

vi.mock('../../src/utils/functionLogSaver', () => ({
  saveFunctionLog: vi.fn(),
  createSuccessLog: vi.fn((fn, year, month, message, data) => ({
    functionName: fn,
    timestamp: new Date(),
    year,
    month,
    success: true,
    message,
    additionalData: data
  })),
  createErrorLog: vi.fn((fn, year, month, error, data) => ({
    functionName: fn,
    timestamp: new Date(),
    year,
    month,
    success: false,
    message: 'スクレイピング処理でエラーが発生しました',
    error,
    additionalData: data
  }))
}))

// オフラインモードで初期化（モックを使用）
const testEnv = firebaseFunctionsTest()

describe('scrapeJRACalendarWithRaceResults', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterAll(() => {
    testEnv.cleanup()
  })

  it('正常なリクエストで成功し、カレンダーとレース結果データを取得・保存できる', async () => {
    // モックモジュールをインポート
    const htmlFetcherModule = await import('../../src/utils/htmlFetcher')
    const firestoreSaverModule = await import('../../src/utils/firestoreSaver')
    const { scrapeJRACalendarWithRaceResults } = await import('../../src/index')

    // モックデータの準備
    const calendarHtmlPath = join(__dirname, '../mock/jra/keiba_calendar2025_oct.html')
    const raceResultHtmlPath = join(__dirname, '../mock/jra/keiba_calendar2025_2025_10_1013.html')
    let mockCalendarHtml = readFileSync(calendarHtmlPath, 'utf-8')
    const mockRaceResultHtml = readFileSync(raceResultHtmlPath, 'utf-8')
    
    // テスト用にround情報を追加（第4回を追加）
    // extractRoundFromCalendarがround情報を見つけられるように、タイトルに追加
    mockCalendarHtml = mockCalendarHtml.replace(
      '<title>レーシングカレンダー　2025年10月　JRA</title>',
      '<title>レーシングカレンダー　2025年10月　JRA</title><h1>第4回</h1>'
    )

    // HTMLフェッチャーをモック設定
    vi.mocked(htmlFetcherModule.fetchJRAHtmlWithPlaywright)
      .mockResolvedValueOnce(mockCalendarHtml) // カレンダーHTML
      .mockResolvedValueOnce(mockRaceResultHtml) // レース結果HTML（1日分）

    // Firestore保存をモック設定
    vi.mocked(firestoreSaverModule.saveRacesToFirestore).mockResolvedValue(10)

    // Express.jsのリクエスト/レスポンスオブジェクトを完全にモック
    const mockRequest = {
      query: { year: '2025', month: '10' },
      body: {},
      headers: {},
      method: 'GET',
      url: '/',
      params: {},
      get: vi.fn(),
      header: vi.fn()
    } as any

    const mockResponse = {
      status: vi.fn().mockReturnThis(),
      send: vi.fn(),
      json: vi.fn(),
      set: vi.fn().mockReturnThis(),
      setHeader: vi.fn().mockReturnThis(),
      getHeader: vi.fn(),
      header: vi.fn().mockReturnThis(),
      on: vi.fn(),
      once: vi.fn(),
      emit: vi.fn(),
      end: vi.fn(),
      write: vi.fn(),
      writeHead: vi.fn(),
      removeHeader: vi.fn(),
      locals: {},
      statusCode: 200
    } as any

    // 関数を実行
    await scrapeJRACalendarWithRaceResults(mockRequest, mockResponse)

    // レスポンスが正常に送信されたことを確認
    expect(mockResponse.status).not.toHaveBeenCalledWith(400)
    expect(mockResponse.status).not.toHaveBeenCalledWith(500)
    expect(mockResponse.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        year: 2025,
        month: 10,
        calendarRacesCount: expect.any(Number),
        raceResultsCount: expect.any(Number),
        totalRacesCount: expect.any(Number)
      })
    )

    // Firestoreへの保存が呼ばれたことを確認
    expect(firestoreSaverModule.saveRacesToFirestore).toHaveBeenCalled()
  })
})

