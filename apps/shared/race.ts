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
  race_key: string  // 場コード_年_回_日_R 形式（JRDB仕様に準拠）
  raceDate: Date
  year?: number     // 年（クエリ用）
  month?: number    // 月（クエリ用）
  racecourse: string
  raceNumber: number
  raceName: string
  grade?: string
  distance?: number
  surface?: string
  weather?: string
  trackCondition?: string
  raceStartTime?: Date | string | any
  results?: RaceResult[]
  scrapedAt: Date
  round?: number | null  // 開催回数（第○回）
}

export interface RaceFilters {
  racecourse?: string
  grade?: string
  surface?: string
  raceDateFrom?: Date
  raceDateTo?: Date
}
