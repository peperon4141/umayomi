// JRAスクレイピング用の型定義
export interface JRARaceData {
  raceNumber: number
  raceName: string
  grade: string
  distance: number
  surface: string
  weather: string
  trackCondition: string
  startTime: string
  description: string
  prize: number
  venue: string
  date: Date
  scrapedAt: Date
}

export interface JRARaceDay {
  date: string
  venue: string
  races: JRARaceData[]
}

export interface JRAMonthData {
  month: string
  year: number
  days: JRARaceDay[]
}
