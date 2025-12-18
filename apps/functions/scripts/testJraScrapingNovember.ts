/**
 * 11月分のJRAデータ取得をテストするスクリプト
 */

import { fetchJRAHtmlWithPlaywright } from '../src/utils/htmlFetcher'
import { parseJRACalendar, extractRaceDates } from '../src/jra_scraper/parser/calendarParser'
import * as cheerio from 'cheerio'
import { parseJRARaceResult } from '../src/jra_scraper/parser/raceResultParser'
import { generateJRACalendarUrl, generateJRARaceResultUrl } from '../src/utils/urlGenerator'

async function testNovemberDataFetch() {
  const year = 2025
  const month = 11
  
  console.log(`=== 11月分のJRAデータ取得テスト ===`)
  console.log(`年: ${year}, 月: ${month}`)
  
  try {
    // 1. カレンダーページを取得
    const calendarUrl = generateJRACalendarUrl(year, month)
    console.log(`\n[1] カレンダーページを取得: ${calendarUrl}`)
    
    const calendarHtml = await fetchJRAHtmlWithPlaywright(calendarUrl)
    console.log(`   HTMLサイズ: ${calendarHtml.length} bytes`)
    
    // 2. カレンダーからレース情報を抽出
    const calendarRaces = parseJRACalendar(calendarHtml, year, month)
    console.log(`\n[2] カレンダーから抽出したレース数: ${calendarRaces.length}`)
    
    // 3. 開催日を抽出
    const $ = cheerio.load(calendarHtml)
    const raceDates = extractRaceDates($, year, month)
    console.log(`\n[3] 抽出した開催日数: ${raceDates.length}`)
    console.log(`   開催日一覧:`)
    raceDates.forEach((date, index) => {
      const day = date.getUTCDate()
      const dateStr = date.toISOString().split('T')[0]
      console.log(`     ${index + 1}. ${dateStr} (${day}日)`)
    })
    
    // 4. 各開催日のレース結果を取得
    console.log(`\n[4] 各開催日のレース結果を取得`)
    const allRaceResults: any[] = []
    const dateResults: { [key: string]: number } = {}
    
    for (const raceDate of raceDates) {
      const day = raceDate.getUTCDate()
      const dateKey = raceDate.toISOString().split('T')[0]
      
      try {
        const raceResultUrl = generateJRARaceResultUrl(year, month, day)
        console.log(`   ${dateKey} (${day}日): ${raceResultUrl}`)
        
        const raceResultHtml = await fetchJRAHtmlWithPlaywright(raceResultUrl)
        const raceResults = parseJRARaceResult(raceResultHtml, year, month, day)
        
        allRaceResults.push(...raceResults)
        dateResults[dateKey] = raceResults.length
        
        console.log(`     → 取得したレース数: ${raceResults.length}`)
        
        // 競馬場ごとのレース数を表示
        const venueCounts: { [key: string]: number } = {}
        raceResults.forEach((race: any) => {
          const venue = race.venue || '不明'
          venueCounts[venue] = (venueCounts[venue] || 0) + 1
        })
        Object.entries(venueCounts).forEach(([venue, count]) => {
          console.log(`       - ${venue}: ${count}レース`)
        })
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        console.error(`     ❌ エラー: ${errorMessage}`)
        dateResults[dateKey] = 0
      }
    }
    
    // 5. 結果サマリー
    console.log(`\n=== 結果サマリー ===`)
    console.log(`カレンダーから抽出したレース数: ${calendarRaces.length}`)
    console.log(`抽出した開催日数: ${raceDates.length}`)
    console.log(`取得したレース結果総数: ${allRaceResults.length}`)
    console.log(`\n開催日ごとのレース数:`)
    Object.entries(dateResults).forEach(([date, count]) => {
      console.log(`  ${date}: ${count}レース`)
    })
    
    // 6. 競馬場ごとの集計
    const venueCounts: { [key: string]: number } = {}
    allRaceResults.forEach((race: any) => {
      const venue = race.venue || '不明'
      venueCounts[venue] = (venueCounts[venue] || 0) + 1
    })
    console.log(`\n競馬場ごとのレース数:`)
    Object.entries(venueCounts).forEach(([venue, count]) => {
      console.log(`  ${venue}: ${count}レース`)
    })
    
    // 7. 問題の検出
    console.log(`\n=== 問題検出 ===`)
    if (raceDates.length === 0) console.log(`❌ 開催日が抽出できていません`)
    if (allRaceResults.length === 0) console.log(`❌ レース結果が取得できていません`)
    const zeroCountDates = Object.entries(dateResults).filter(([_, count]) => count === 0)
    if (zeroCountDates.length > 0) {
      console.log(`❌ レースが取得できなかった日付:`)
      zeroCountDates.forEach(([date]) => {
        console.log(`     - ${date}`)
      })
    }
    
    const expectedNovemberDates = [
      '2025-11-01', '2025-11-02', '2025-11-03', '2025-11-09', '2025-11-10',
      '2025-11-16', '2025-11-17', '2025-11-23', '2025-11-24', '2025-11-29', '2025-11-30'
    ]
    const extractedDates = raceDates.map(d => d.toISOString().split('T')[0])
    const missingDates = expectedNovemberDates.filter(d => !extractedDates.includes(d))
    if (missingDates.length > 0) {
      console.log(`❌ 期待される開催日が抽出されていません:`)
      missingDates.forEach(date => {
        console.log(`     - ${date}`)
      })
    }
    
  } catch (error) {
    console.error('テスト実行エラー:', error)
    process.exit(1)
  }
}

// スクリプト実行
testNovemberDataFetch()
  .then(() => {
    console.log('\n✅ テスト完了')
    process.exit(0)
  })
  .catch((error) => {
    console.error('テスト失敗:', error)
    process.exit(1)
  })

