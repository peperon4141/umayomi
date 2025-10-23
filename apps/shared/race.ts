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
  grade: string
  distance: number
  surface: string
  weather: string
  trackCondition: string
  results: RaceResult[]
  scrapedAt: Date
}

export interface RaceFilters {
  racecourse?: string
  grade?: string
  surface?: string
  dateFrom?: Date
  dateTo?: Date
}
