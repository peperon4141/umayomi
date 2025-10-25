#!/usr/bin/env tsx

/**
 * JRAスクレイピングテストスクリプト
 * 実際にJRAの10月開催日程からレース情報を取得して確認する
 */

import { scrapeJRAData } from '../src/scraper/jraScraper'

async function main() {
  console.log('🚀 JRAスクレイピングテストを開始します...')
  console.log('📅 対象: 2024年10月の開催日程')
  console.log('🌐 URL: https://www.jra.go.jp/keiba/calendar/oct.html')
  console.log('')

  try {
    const startTime = Date.now()
    
    // JRAスクレイピング実行
    const races = await scrapeJRAData()
    
    const endTime = Date.now()
    const duration = endTime - startTime

    console.log('✅ スクレイピング完了!')
    console.log(`⏱️  実行時間: ${duration}ms`)
    console.log(`📊 取得レース数: ${races.length}件`)
    console.log('')

    if (races.length === 0) {
      console.log('⚠️  レースデータが取得できませんでした')
      console.log('🔍 可能性のある原因:')
      console.log('   - ネットワーク接続の問題')
      console.log('   - JRAサイトの構造変更')
      console.log('   - 10月の開催日程が未公開')
      return
    }

    // レース情報を日付でグループ化
    const racesByDate = races.reduce((acc: Record<string, any[]>, race) => {
      const dateStr = race.date instanceof Date 
        ? race.date.toLocaleDateString('ja-JP')
        : '日付不明'
      
      if (!acc[dateStr]) {
        acc[dateStr] = []
      }
      acc[dateStr].push(race)
      return acc
    }, {})

    // 結果を表示
    console.log('📋 取得したレース情報:')
    console.log('=' .repeat(80))
    
    Object.entries(racesByDate).forEach(([date, dayRaces]) => {
      console.log(`\n🗓️  ${date} (${dayRaces.length}レース)`)
      console.log('-'.repeat(60))
      
      dayRaces.forEach((race, index) => {
        console.log(`${index + 1}. ${race.raceName}`)
        console.log(`   🏟️  競馬場: ${race.venue}`)
        console.log(`   🏆 グレード: ${race.grade}`)
        console.log(`   🏃 コース: ${race.surface}`)
        console.log(`   📏 距離: ${race.distance}m`)
        console.log(`   ⏰ 発走時刻: ${race.startTime}`)
        console.log(`   📝 詳細: ${race.description}`)
        console.log('')
      })
    })

    // 統計情報
    console.log('📊 統計情報:')
    console.log('=' .repeat(40))
    
    const racecourses = [...new Set(races.map(r => r.venue))].filter(Boolean)
    const grades = [...new Set(races.map(r => r.grade))].filter(Boolean)
    const surfaces = [...new Set(races.map(r => r.surface))].filter(Boolean)
    
    console.log(`🏟️  競馬場: ${racecourses.join(', ')}`)
    console.log(`🏆 グレード: ${grades.join(', ')}`)
    console.log(`🏃 コース: ${surfaces.join(', ')}`)
    
    const totalDistance = races.reduce((sum, race) => sum + (race.distance || 0), 0)
    const avgDistance = races.length > 0 ? Math.round(totalDistance / races.length) : 0
    console.log(`📏 平均距離: ${avgDistance}m`)

    console.log('')
    console.log('✅ テスト完了!')

  } catch (error) {
    console.error('❌ エラーが発生しました:')
    console.error(error)
    process.exit(1)
  }
}

// スクリプト実行
if (require.main === module) {
  main().catch(console.error)
}
