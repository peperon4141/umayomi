/**
 * レースグレードエンティティ
 */
export enum RaceGrade {
  G1 = 'GⅠ',
  G2 = 'GⅡ',
  G3 = 'GⅢ',
  L = 'L',
  OP = 'OP',
  G3_SPECIAL = 'G3特別',
  L_SPECIAL = 'L特別',
  ALLOWANCE = '条件',
  MAIDEN = '未勝利',
  NEWCOMER = '新馬',
  JUVENILE = '2歳',
  JUVENILE_FILLIES = '2歳牝馬',
  JUVENILE_COLT = '2歳牡馬'
}

/**
 * レースグレードの重要度
 */
export const GRADE_IMPORTANCE: Record<RaceGrade, number> = {
  [RaceGrade.G1]: 5,
  [RaceGrade.G2]: 4,
  [RaceGrade.G3]: 3,
  [RaceGrade.L]: 2,
  [RaceGrade.OP]: 1,
  [RaceGrade.G3_SPECIAL]: 2,
  [RaceGrade.L_SPECIAL]: 1,
  [RaceGrade.ALLOWANCE]: 0,
  [RaceGrade.MAIDEN]: 0,
  [RaceGrade.NEWCOMER]: 0,
  [RaceGrade.JUVENILE]: 0,
  [RaceGrade.JUVENILE_FILLIES]: 0,
  [RaceGrade.JUVENILE_COLT]: 0
}

/**
 * レースグレードの色
 */
export const GRADE_COLORS: Record<RaceGrade, string> = {
  [RaceGrade.G1]: 'danger',
  [RaceGrade.G2]: 'warning',
  [RaceGrade.G3]: 'info',
  [RaceGrade.L]: 'success',
  [RaceGrade.OP]: 'secondary',
  [RaceGrade.G3_SPECIAL]: 'info',
  [RaceGrade.L_SPECIAL]: 'success',
  [RaceGrade.ALLOWANCE]: 'secondary',
  [RaceGrade.MAIDEN]: 'secondary',
  [RaceGrade.NEWCOMER]: 'secondary',
  [RaceGrade.JUVENILE]: 'secondary',
  [RaceGrade.JUVENILE_FILLIES]: 'secondary',
  [RaceGrade.JUVENILE_COLT]: 'secondary'
}
