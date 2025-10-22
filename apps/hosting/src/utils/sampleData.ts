import { Timestamp } from 'firebase/firestore'
import type { Race } from '@/types/race'

export const sampleRaces: Race[] = [
  {
    id: 'race-001',
    raceId: 'race-001',
    date: Timestamp.fromDate(new Date('2025-10-05T14:00:00Z')),
    racecourse: '東京',
    raceNumber: 1,
    raceName: '新馬戦',
    grade: '新馬',
    surface: '芝',
    distance: 1600,
    weather: '晴',
    trackCondition: '良',
    results: [
      { rank: 1, horseName: 'サンプルホース1', horseNumber: 1, jockey: '騎手A', odds: 2.5, time: '1:23.4' },
      { rank: 2, horseName: 'サンプルホース2', horseNumber: 2, jockey: '騎手B', odds: 3.2, time: '1:23.8' },
      { rank: 3, horseName: 'サンプルホース3', horseNumber: 3, jockey: '騎手C', odds: 4.1, time: '1:24.1' }
    ],
    scrapedAt: Timestamp.now()
  },
  {
    id: 'race-002',
    raceId: 'race-002',
    date: Timestamp.fromDate(new Date('2025-10-05T15:00:00Z')),
    racecourse: '中山',
    raceNumber: 2,
    raceName: '条件戦',
    grade: '条件',
    surface: '芝',
    distance: 2000,
    weather: '晴',
    trackCondition: '良',
    results: [
      { rank: 1, horseName: 'テストホース1', horseNumber: 1, jockey: '騎手D', odds: 1.8, time: '2:05.2' },
      { rank: 2, horseName: 'テストホース2', horseNumber: 2, jockey: '騎手E', odds: 2.9, time: '2:05.8' },
      { rank: 3, horseName: 'テストホース3', horseNumber: 3, jockey: '騎手F', odds: 5.2, time: '2:06.1' }
    ],
    scrapedAt: Timestamp.now()
  }
]

// サンプルデータをFirestoreに保存する関数
export async function seedRaceData() {
  // 実際の実装は後で追加
  console.log('サンプルデータを投入中...')
  return Promise.resolve()
}

// Firestoreのデータをクリアする関数
export async function clearRaceData() {
  // 実際の実装は後で追加
  console.log('データをクリア中...')
  return Promise.resolve()
}