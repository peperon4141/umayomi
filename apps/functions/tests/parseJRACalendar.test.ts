import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'
import { parseJRACalendar, extractRaceElements, parseRaceElement, extractRaceDates } from '../src/parser/jra/calendarParser'

describe('parseJRACalendar', () => {
  describe('2025年10月', () => {
    // テスト用のHTMLファイルと期待値を読み込み
    const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_oct.html')
    const expectedPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_oct_expected.json')
    
    const htmlContent = readFileSync(htmlPath, 'utf-8')
    const expectedData = JSON.parse(readFileSync(expectedPath, 'utf-8'))

    it('HTMLからレース情報を正しく抽出できる', () => {
      const result = parseJRACalendar(htmlContent, 2025, 10)
      
      // 結果が期待値と一致することを確認
      expect(result).toBeDefined()
      expect(result.length).toBeGreaterThan(0)
      
      // 期待値のレース名が含まれていることを確認
      const resultRaceNames = result.map((race: any) => race.raceName)
      const expectedRaceNames = expectedData.races.map((race: any) => race.raceName)
      
      expectedRaceNames.forEach((expectedName: string) => {
        expect(resultRaceNames).toContain(expectedName)
      })
    })
  })

  describe('2025年9月', () => {
    const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_sep.html')
    const expectedPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_sep_expected.json')
    
    const htmlContent = readFileSync(htmlPath, 'utf-8')
    const expectedData = JSON.parse(readFileSync(expectedPath, 'utf-8'))

    it('9月のHTMLから9日間のレース情報を正しく抽出できる', () => {
      const result = parseJRACalendar(htmlContent, 2025, 9)
      
      // 結果が期待値と一致することを確認
      expect(result).toBeDefined()
      expect(result.length).toBe(expectedData.racesCount)
      
      // 期待値のレース名が含まれていることを確認
      const resultRaceNames = result.map((race: any) => race.raceName)
      const expectedRaceNames = expectedData.races.map((race: any) => race.raceName)
      
      expectedRaceNames.forEach((expectedName: string) => {
        expect(resultRaceNames).toContain(expectedName)
      })
    })
  })
})

describe('extractRaceElements', () => {
  const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_oct.html')
  const htmlContent = readFileSync(htmlPath, 'utf-8')

  it('HTMLからレース要素を正しく抽出できる', () => {
    const cheerio = require('cheerio')
    const $ = cheerio.load(htmlContent)
    const elements = extractRaceElements($)
    
    expect(elements).toBeDefined()
    expect(Array.isArray(elements)).toBe(true)
    expect(elements.length).toBeGreaterThan(0)
  })

  it('抽出された要素にレース名が含まれている', () => {
    const cheerio = require('cheerio')
    const $ = cheerio.load(htmlContent)
    const elements = extractRaceElements($)
    
    // レース名が含まれる要素が存在することを確認
    const hasRaceName = elements.some(element => {
      const text = element.text()
      return text.includes('毎日王冠') || 
             text.includes('京都大賞典') ||
             text.includes('秋華賞') ||
             text.includes('菊花賞')
    })
    
    expect(hasRaceName).toBe(true)
  })
})

describe('parseRaceElement', () => {
  it('無効な要素の場合はnullを返す', () => {
    const cheerio = require('cheerio')
    const $ = cheerio.load('<div class="other">無関係なコンテンツ</div>')
    const element = $('div')
    const result = parseRaceElement($, element, 0, 2025, 10)
    
    expect(result).toBeNull()
  })
})

describe('extractRaceDates', () => {
  describe('2025年9月', () => {
    const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_sep.html')
    const htmlContent = readFileSync(htmlPath, 'utf-8')

    it('9月のHTMLから9日間の開催日を正しく抽出できる', () => {
      const cheerio = require('cheerio')
      const $ = cheerio.load(htmlContent)
      const dates = extractRaceDates($, 2025, 9)
      
      expect(dates).toBeDefined()
      expect(Array.isArray(dates)).toBe(true)
      expect(dates.length).toBe(9)
      
      // 期待される開催日: 6, 7, 13, 14, 15, 20, 21, 27, 28日
      const expectedDays = [6, 7, 13, 14, 15, 20, 21, 27, 28]
      const resultDays = dates.map(date => date.getUTCDate())
      
      expectedDays.forEach(expectedDay => {
        expect(resultDays).toContain(expectedDay)
      })
      
      expect(resultDays.length).toBe(expectedDays.length)
    })
  })

  describe('2025年10月', () => {
    const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_oct.html')
    const htmlContent = readFileSync(htmlPath, 'utf-8')

    it('10月のHTMLから開催日を正しく抽出できる', () => {
      const cheerio = require('cheerio')
      const $ = cheerio.load(htmlContent)
      const dates = extractRaceDates($, 2025, 10)
      
      expect(dates).toBeDefined()
      expect(Array.isArray(dates)).toBe(true)
      expect(dates.length).toBeGreaterThan(0)
      
      // 日付が正しくソートされていることを確認
      for (let i = 1; i < dates.length; i++) {
        expect(dates[i].getTime()).toBeGreaterThanOrEqual(dates[i - 1].getTime())
      }
    })
  })
})

