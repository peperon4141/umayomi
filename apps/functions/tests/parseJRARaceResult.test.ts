import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'
import * as cheerio from 'cheerio'
import { parseJRARaceResult, extractRaceInfo } from '../src/parser/jra/raceResultParser'

describe('parseJRARaceResult', () => {
  // テスト用のHTMLファイルと期待値を読み込み
  const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_2025_10_1013.html')
  const expectedPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_2025_10_1013_expected.json')

  const htmlContent = readFileSync(htmlPath, 'utf-8')
  const expectedData = JSON.parse(readFileSync(expectedPath, 'utf-8'))

  it('HTMLからレース情報を正しく抽出できる', () => {
    const result = parseJRARaceResult(htmlContent, 2025, 10, 13)

    // 結果が期待値と一致することを確認
    expect(result).toBeDefined()
    expect(result.length).toBeGreaterThan(0)
    expect(result.length).toBe(expectedData.races.length)

    // 期待値のレース名が含まれていることを確認
    const resultRaceNames = result.map((race: any) => race.raceName)
    const expectedRaceNames = expectedData.races.map((race: any) => race.raceName)

    expectedRaceNames.forEach((expectedName: string) => {
      expect(resultRaceNames).toContain(expectedName)
    })

    // 期待値の競馬場が含まれていることを確認
    const resultVenues = result.map((race: any) => race.venue)
    const expectedVenues = expectedData.races.map((race: any) => race.venue)

    expectedVenues.forEach((expectedVenue: string) => {
      expect(resultVenues).toContain(expectedVenue)
    })

    // 期待値の距離が正しいことを確認
    result.forEach((race: any) => {
      const expectedRace = expectedData.races.find((r: any) => 
        r.raceName === race.raceName && r.venue === race.venue && r.raceNumber === race.raceNumber
      )
      if (expectedRace) {
        expect(race.distance).toBe(expectedRace.distance)
        expect(race.surface).toBe(expectedRace.surface)
                expect(new Date(race.startTime).toISOString()).toBe(new Date(expectedRace.startTime).toISOString())
      }
    })
  })
})

describe('extractRaceInfo', () => {
  const htmlPath = join(__dirname, 'mock', 'jra', 'keiba_calendar2025_2025_10_1013.html')
  const htmlContent = readFileSync(htmlPath, 'utf-8')

  it('HTMLからレース情報を正しく抽出できる', () => {
    const $ = cheerio.load(htmlContent)
    const raceInfo = extractRaceInfo($)

    expect(raceInfo).toBeDefined()
    expect(raceInfo.length).toBeGreaterThan(0)
  })

  it('抽出された要素にレース名が含まれている', () => {
    const $ = cheerio.load(htmlContent)
    const raceInfo = extractRaceInfo($)

    // レース名が含まれる要素が存在することを確認
    const hasRaceName = raceInfo.some((race: any) => {
      return race.raceName.includes('2歳未勝利') ||
             race.raceName.includes('プラタナス賞') ||
             race.raceName.includes('スワンステークス')
    })

    expect(hasRaceName).toBe(true)
  })
})

