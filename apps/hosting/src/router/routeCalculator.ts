/**
 * ルート計算ユーティリティ
 * URL生成とナビゲーション用の計算ロジックを提供
 */

import { getVenueIdFromName } from '@/entity'

// ルート名のenum定義（循環importを避けるため）
export enum RouteName {
  // 基本ページ
  HOME = 'Home',
  ADMIN_DASHBOARD = 'AdminDashboard',
  RACES = 'Races',
  
  // レース関連（直接アクセス）
  RACE_DETAIL_DIRECT = 'RaceDetailDirect',
  
  // レース関連（階層構造）
  RACE_LIST = 'RaceList',
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
  [RouteName.ADMIN_DASHBOARD]: () => '/admin',
  [RouteName.RACES]: () => '/races',
  [RouteName.RACE_LIST]: () => '/race-list',
  [RouteName.RACE_DETAIL_DIRECT]: (options: RouteOptions) => `/race/${options.raceId}`,
  [RouteName.RACE_LIST_IN_DAY]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/day/${options.day}`,
  [RouteName.RACE_LIST_IN_DAY_PLACE]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/day/${options.day}?placeId=${options.placeId}`,
  [RouteName.RACE_LIST_IN_PLACE]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/place/${options.placeId}`,
  [RouteName.RACE_DETAIL]: (options: RouteOptions) => `/races/year/${options.year}/month/${options.month}/place/${options.placeId}/race/${options.raceId}`,
} as const

// 必須パラメータの検証
const validateOptions = (routeName: RouteName, options: RouteOptions): void => {
  const validators: Partial<Record<RouteName, () => string | false>> = {
    [RouteName.RACE_DETAIL_DIRECT]: () => !options.raceId && 'raceId is required',
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

