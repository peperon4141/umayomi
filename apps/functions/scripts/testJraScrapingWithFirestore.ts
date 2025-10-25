#!/usr/bin/env tsx

/**
 * JRAスクレイピング + Firestore保存テストスクリプト
 * 実際にJRAの10月開催日程からレース情報を取得してFirestoreに保存する
 */

import { initializeApp } from 'firebase-admin/app'
import { getFirestore, Timestamp } from 'firebase-admin/firestore'
import { scrapeJRAData } from '../src/scraper/jraScraper'
import type { JRARaceData } from '../../shared/jra'

// Firebase Admin SDKを初期化（エミュレーター用）
process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
process.env.GCLOUD_PROJECT = 'umayomi-fbb2b'
initializeApp()
const db = getFirestore()

async function main() {
  console.log('🚀 JRAスクレイピング + Firestore保存テストを開始します...')
  console.log('📅 対象: 2024年10月の開催日程')
  console.log('🌐 URL: https://www.jra.go.jp/keiba/calendar/oct.html')
  console.log('🔥 Firestore Emulator: 127.0.0.1:8180')
  console.log('')

  try {
    const startTime = Date.now()
    
    // JRAスクレイピング実行
    console.log('📡 スクレイピングを開始...')
    const races = await scrapeJRAData()
    
    const scrapingTime = Date.now()
    console.log(`✅ スクレイピング完了! (${scrapingTime - startTime}ms)`)
    console.log(`📊 取得レース数: ${races.length}件`)
    console.log('')

    if (races.length === 0) {
      console.log('⚠️  レースデータが取得できませんでした')
      return
    }

    // Firestoreに保存
    console.log('🔥 Firestoreに保存を開始...')
    const savedCount = await saveRacesToFirestore(races)
    
    const endTime = Date.now()
    const totalDuration = endTime - startTime
    const saveDuration = endTime - scrapingTime

    console.log('✅ Firestore保存完了!')
    console.log(`⏱️  総実行時間: ${totalDuration}ms`)
    console.log(`⏱️  保存時間: ${saveDuration}ms`)
    console.log(`📊 保存レース数: ${savedCount}件`)
    console.log('')

    // 保存されたデータを確認
    console.log('🔍 保存されたデータを確認...')
    const savedRaces = await getSavedRaces()
    console.log(`📋 Firestore内のレース数: ${savedRaces.length}件`)
    
    if (savedRaces.length > 0) {
      console.log('📝 最初のレース情報:')
      const firstRace = savedRaces[0]
      console.log(`   🏟️  競馬場: ${firstRace.racecourse}`)
      console.log(`   🏆 グレード: ${firstRace.grade}`)
      console.log(`   🏃 コース: ${firstRace.surface}`)
      console.log(`   📏 距離: ${firstRace.distance}m`)
      console.log(`   ⏰ 発走時刻: ${firstRace.startTime}`)
      console.log(`   📅 日付: ${firstRace.date?.toDate?.()?.toLocaleDateString('ja-JP') || '日付不明'}`)
    }

    console.log('')
    console.log('✅ テスト完了!')

  } catch (error) {
    console.error('❌ エラーが発生しました:')
    console.error(error)
    process.exit(1)
  }
}

/**
 * Firestoreにレースデータを保存
 */
async function saveRacesToFirestore(races: JRARaceData[]): Promise<number> {
  if (races.length === 0) return 0
  
  const batch = db.batch()
  let savedCount = 0
  
  for (const race of races) {
    try {
      const docRef = db.collection('races').doc()
      batch.set(docRef, {
        ...race,
        date: race.date && !isNaN(race.date.getTime()) ? Timestamp.fromDate(race.date) : null,
        scrapedAt: Timestamp.fromDate(race.scrapedAt)
      })
      savedCount++
    } catch (error) {
      console.error('Error saving race to Firestore', { race, error })
    }
  }
  
  try {
    await batch.commit()
    console.log(`✅ バッチコミット完了: ${savedCount}件`)
  } catch (error) {
    console.error('❌ バッチコミットエラー:', error)
    throw error
  }
  
  return savedCount
}

/**
 * 保存されたレースデータを取得
 */
async function getSavedRaces(): Promise<any[]> {
  try {
    const snapshot = await db.collection('races').limit(10).get()
    return snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data()
    }))
  } catch (error) {
    console.error('Error getting saved races:', error)
    return []
  }
}

// スクリプト実行
if (require.main === module) {
  main().catch(console.error)
}
