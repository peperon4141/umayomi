/**
 * 競馬場エンティティ
 */
export enum Venue {
  TOKYO = 'tokyo',
  NAKAYAMA = 'nakayama',
  KYOTO = 'kyoto',
  HANSHIN = 'hanshin',
  NIIGATA = 'niigata',
  KOKURA = 'kokura',
  FUKUSHIMA = 'fukushima',
  CHUKYO = 'chukyo',
  HAKODATE = 'hakodate',
  SAPPORO = 'sapporo'
}

/**
 * 競馬場の日本語名マッピング
 */
export const VENUE_NAMES: Record<Venue, string> = {
  [Venue.TOKYO]: '東京競馬場',
  [Venue.NAKAYAMA]: '中山競馬場',
  [Venue.KYOTO]: '京都競馬場',
  [Venue.HANSHIN]: '阪神競馬場',
  [Venue.NIIGATA]: '新潟競馬場',
  [Venue.KOKURA]: '小倉競馬場',
  [Venue.FUKUSHIMA]: '福島競馬場',
  [Venue.CHUKYO]: '中京競馬場',
  [Venue.HAKODATE]: '函館競馬場',
  [Venue.SAPPORO]: '札幌競馬場'
}

/**
 * 日本語名から競馬場IDを取得
 */
export const getVenueIdFromName = (venueName: string): Venue | null => {
  const entry = Object.entries(VENUE_NAMES).find(([, name]) => name === venueName)
  return entry ? (entry[0] as Venue) : null
}

/**
 * 競馬場IDから日本語名を取得
 */
export const getVenueNameFromId = (venueId: Venue): string => {
  return VENUE_NAMES[venueId] || venueId
}
