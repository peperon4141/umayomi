// JRAスクレイピング用の型定義
export interface JRARaceData {
  raceNumber: number
  raceName: string
  grade: string
  distance: number
  surface: string
  weather: string
  trackCondition: string
  raceStartTime: string
  description: string
  prize: number
  venue: string
  raceDate: Date
  scrapedAt: Date
}

export interface JRARaceDay {
  raceDate: string
  venue: string
  races: JRARaceData[]
}

export interface JRAMonthData {
  month: string
  year: number
  days: JRARaceDay[]
}
