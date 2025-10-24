/**
 * レースコース表面エンティティ
 */
export enum RaceSurface {
  TURF = '芝',
  DIRT = 'ダート',
  ALL_WEATHER = 'オールウェザー'
}

/**
 * レースコース表面の色
 */
export const SURFACE_COLORS: Record<RaceSurface, string> = {
  [RaceSurface.TURF]: 'success',
  [RaceSurface.DIRT]: 'warning',
  [RaceSurface.ALL_WEATHER]: 'info'
}
