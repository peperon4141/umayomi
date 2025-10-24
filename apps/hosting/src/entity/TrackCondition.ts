/**
 * 馬場状態エンティティ
 */
export enum TrackCondition {
  FIRM = '良',
  GOOD = '稍重',
  YIELDING = '重',
  SOFT = '不良'
}

/**
 * 馬場状態の色
 */
export const TRACK_CONDITION_COLORS: Record<TrackCondition, string> = {
  [TrackCondition.FIRM]: 'success',
  [TrackCondition.GOOD]: 'warning',
  [TrackCondition.YIELDING]: 'warning',
  [TrackCondition.SOFT]: 'danger'
}
