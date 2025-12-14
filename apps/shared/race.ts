export interface RaceResult {
  rank: number
  horseNumber: number
  horseName: string
  jockey: string
  time: string
  odds: number
}

export interface Race {
  id: string
  raceId: string
  date: Date
  racecourse: string
  raceNumber: number
  raceName: string
  grade?: string
  distance?: number
  surface?: string
  weather?: string
  trackCondition?: string
  startTime?: Date | string | any
  results?: RaceResult[]
  scrapedAt: Date
  round?: number | null  // 開催回数（第○回）
  day?: string | null     // 日目（1, 2, 3, ..., a, b, cなど）
}

export interface RaceFilters {
  racecourse?: string
  grade?: string
  surface?: string
  dateFrom?: Date
  dateTo?: Date
}
