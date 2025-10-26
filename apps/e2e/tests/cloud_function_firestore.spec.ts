import { test, expect } from '@playwright/test'

test.describe('Cloud Functions', () => {
  test('helloWorld関数を呼び出してHelloWorldを取得できる', async ({ request }) => {
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/helloWorld')

    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.message).toBe('HelloWorld')
    expect(data.timestamp).toBeDefined()
  })

  test('scrapeJRACalendar関数を呼び出してデータを取得できる', async ({ request }) => {
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendar', {
      params: {
        year: '2025',
        month: '10'
      }
    })

    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.message).toContain('2025年10月のJRAデータの取得・保存が完了しました')
    expect(data.racesCount).toBeGreaterThan(0)
    expect(data.savedCount).toBeGreaterThan(0)
    expect(data.url).toBe('https://www.jra.go.jp/keiba/calendar2025/oct.html')
    expect(data.year).toBe(2025)
    expect(data.month).toBe(10)
  })

  test('scrapeJRARaceResult関数を呼び出してレース結果データを取得できる', async ({ request }) => {
    const response = await request.get('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRARaceResult', {
      params: {
        year: '2025',
        month: '10',
        day: '13'
      }
    })

    expect(response.status()).toBe(200)
    
    const data = await response.json()
    expect(data.success).toBe(true)
    expect(data.message).toContain('2025年10月13日のJRAレース結果データの取得・保存が完了しました')
    expect(data.racesCount).toBeGreaterThan(0)
    expect(data.savedCount).toBeGreaterThan(0)
    expect(data.url).toBe('https://www.jra.go.jp/keiba/calendar2025/2025/10/1013.html')
    expect(data.year).toBe(2025)
    expect(data.month).toBe(10)
    expect(data.day).toBe(13)
  })
})
