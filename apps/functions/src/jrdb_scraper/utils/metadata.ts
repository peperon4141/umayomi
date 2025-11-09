/**
 * メタデータ作成ユーティリティ
 */

/**
 * Storage用のメタデータを作成
 */
export function createStorageMetadata(
  fileName: string,
  sourceUrl: string,
  dataType: string,
  date: string
): Record<string, string> {
  return {
    fileName,
    sourceUrl: sourceUrl || '',
    dataType,
    date
  }
}

/**
 * Firestore用のメタデータを作成
 */
export function createFirestoreMetadata(
  dataType: string,
  date: string,
  year: number,
  month: number,
  day: number,
  lzhStoragePath: string | undefined,
  npzStoragePath: string,
  jsonStoragePath: string,
  fileName: string,
  recordCount: number
): Record<string, unknown> {
  return {
    dataType,
    date,
    year,
    month,
    day,
    lzhStoragePath,
    npzStoragePath,
    jsonStoragePath,
    fileName,
    recordCount,
    fetchedAt: new Date()
  }
}

