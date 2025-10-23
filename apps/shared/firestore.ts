// Firestore用の型定義
export interface FirestoreRace {
  id: string
  raceId: string
  date: any // Firestore Timestamp
  racecourse: string
  raceNumber: number
  raceName: string
  grade: string
  distance: number
  surface: string
  weather: string
  trackCondition: string
  results: any[] // Firestore用の配列
  scrapedAt: any // Firestore Timestamp
}

export interface FirestoreUser {
  uid: string
  email: string
  displayName?: string
  role: string
  createdAt: any // Firestore Timestamp
  lastLoginAt?: any // Firestore Timestamp
}
