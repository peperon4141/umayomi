/**
 * 天候エンティティ
 */
export enum Weather {
  SUNNY = '晴',
  CLOUDY = '曇',
  RAINY = '雨',
  SNOWY = '雪',
  FOGGY = '霧'
}

/**
 * 天候の色
 */
export const WEATHER_COLORS: Record<Weather, string> = {
  [Weather.SUNNY]: 'warning',
  [Weather.CLOUDY]: 'secondary',
  [Weather.RAINY]: 'info',
  [Weather.SNOWY]: 'primary',
  [Weather.FOGGY]: 'secondary'
}
