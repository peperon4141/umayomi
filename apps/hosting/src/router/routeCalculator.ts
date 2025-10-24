/**
 * ルート計算ユーティリティ
 * URL生成とナビゲーション用の計算ロジックを提供
 */

import { getVenueIdFromName } from '@/entity'

// ルート名のenum定義（循環importを避けるため）
export enum RouteName {
  // 基本ページ
  HOME = 'Home',
  DASHBOARD = 'Dashboard',
  ADMIN_DASHBOARD = 'AdminDashboard',
  
  // レース関連（直接アクセス）
  RACE_DETAIL_DIRECT = 'RaceDetailDirect',
  
  // レース関連（階層構造）
  RACE_LIST_IN_YEAR = 'RaceListInYear',
  RACE_LIST_IN_MONTH = 'RaceListInMonth',
  RACE_LIST_IN_DAY = 'RaceListInDay',
  RACE_LIST_IN_DAY_PLACE = 'RaceListInDayPlace',
  RACE_LIST_IN_PLACE = 'RaceListInPlace',
  RACE_DETAIL = 'RaceDetail',
}

// 日付計算ユーティリティ
export const getCurrentYear = (): number => new Date().getFullYear()
export const getCurrentMonth = (): number => new Date().getMonth() + 1

// 競馬場ID変換ユーティリティ
export const convertVenueToId = (venue: string): string => {
  const venueId = getVenueIdFromName(venue)
  return venueId || venue.toLowerCase().replace('競馬場', '')
}

// ルート生成オプションの型定義
export interface RouteOptions {
  year?: number
  month?: number
  day?: number
  placeId?: string
  raceId?: string
}

// ルート生成のマッピング
const ROUTE_PATTERNS = {
  [RouteName.HOME]: () => '/',
  [RouteName.DASHBOARD]: () => '/dashboard',
  [RouteName.ADMIN_DASHBOARD]: () => '/admin',
  [RouteName.RACE_DETAIL_DIRECT]: (options: RouteOptions) => `/race/${options.raceId}`,
  [RouteName.RACE_LIST_IN_YEAR]: (options: RouteOptions) => `/races/year/${options.year}`,
  [RouteName.RACE_LIST_IN_MONTH]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}`,
  [RouteName.RACE_LIST_IN_DAY]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/day/${options.day}`,
  [RouteName.RACE_LIST_IN_DAY_PLACE]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/day/${options.day}?placeId=${options.placeId}`,
  [RouteName.RACE_LIST_IN_PLACE]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/place/${options.placeId}`,
  [RouteName.RACE_DETAIL]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/place/${options.placeId}/race/${options.raceId}`,
} as const

// 必須パラメータの検証
const validateOptions = (routeName: RouteName, options: RouteOptions): void => {
  const validators: Partial<Record<RouteName, () => string | false>> = {
    [RouteName.RACE_DETAIL_DIRECT]: () => !options.raceId && 'raceId is required',
    [RouteName.RACE_LIST_IN_YEAR]: () => !options.year && 'year is required',
    [RouteName.RACE_LIST_IN_MONTH]: () => (!options.year || !options.month) && 'year and month are required',
    [RouteName.RACE_LIST_IN_DAY]: () => (!options.year || !options.month || !options.day) && 'year, month, and day are required',
    [RouteName.RACE_LIST_IN_DAY_PLACE]: () => (!options.year || !options.month || !options.day || !options.placeId) && 'year, month, day, and placeId are required',
    [RouteName.RACE_LIST_IN_PLACE]: () => (!options.year || !options.month || !options.placeId) && 'year, month, and placeId are required',
    [RouteName.RACE_DETAIL]: () => (!options.year || !options.month || !options.placeId || !options.raceId) && 'year, month, placeId, and raceId are required',
  }
  
  const error = validators[routeName]?.()
  if (error) throw new Error(error)
}

// enumベースのルート生成
export const generateRoute = (routeName: RouteName, options: RouteOptions = {}): string => {
  validateOptions(routeName, options)
  return ROUTE_PATTERNS[routeName](options)
}

// 便利なヘルパー関数
export const getCurrentYearRoute = (): string => 
  generateRoute(RouteName.RACE_LIST_IN_YEAR, { year: getCurrentYear() })

export const getCurrentMonthRoute = (): string => 
  generateRoute(RouteName.RACE_LIST_IN_MONTH, { 
    year: getCurrentYear(), 
    month: getCurrentMonth() 
  })

// 日付からルート生成
export const getRouteFromDate = (date: Date): string => 
  generateRoute(RouteName.RACE_LIST_IN_MONTH, {
    year: date.getFullYear(),
    month: date.getMonth() + 1
  })

export const getCurrentDateRoute = (): string => getRouteFromDate(new Date())

// 後方互換性のための関数（非推奨）
export const getCurrentYearRedirect = getCurrentYearRoute
export const getCurrentMonthRedirect = getCurrentMonthRoute
export const getRaceYearRoute = (year: number): string =>
  generateRoute(RouteName.RACE_LIST_IN_YEAR, { year })
export const getRaceMonthRoute = (year: number, month: number): string =>
  generateRoute(RouteName.RACE_LIST_IN_MONTH, { year, month })
export const getRaceDateRoute = (year: number, month: number, placeId: string): string =>
  generateRoute(RouteName.RACE_LIST_IN_PLACE, { year, month, placeId })
export const getRaceDetailRoute = (year: number, month: number, placeId: string, raceId: string): string =>
  generateRoute(RouteName.RACE_DETAIL, { year, month, placeId, raceId })
export const getDirectRaceDetailRoute = (raceId: string): string =>
  generateRoute(RouteName.RACE_DETAIL_DIRECT, { raceId })

