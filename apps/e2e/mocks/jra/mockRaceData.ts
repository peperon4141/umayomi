import type { JRARaceData } from '../../shared/jra'

export const mockRaceData: JRARaceData[] = [
  {
    raceName: 'テストレース1',
    racecourse: '東京',
    raceDate: new Date('2024-10-15'),
    grade: 'G1',
    surface: '芝',
    distance: 2000,
    age: 3,
    raceStartTime: '15:40',
    prize: 100000000,
    description: 'テストレースの説明',
    source: 'Mock Data',
    scrapedAt: new Date('2024-10-15T10:00:00Z')
  }
]
