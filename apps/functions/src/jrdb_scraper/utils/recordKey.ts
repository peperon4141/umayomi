/**
 * レコードキー生成ユーティリティ
 */

/**
 * レコードからFirestoreのドキュメントIDとして使用可能なキーを生成
 */
export function generateRecordKey(record: Record<string, unknown>, index: number): string {
  const keyFields = [
    'レースキー',
    '血統登録番号',
    '競走成績キー',
    '騎手コード',
    '調教師コード',
    'レース番号',
    '日付'
  ]

  for (const field of keyFields) {
    const value = record[field]
    if (value && typeof value === 'string' && value.trim() !== '') return sanitizeRecordKey(value)
  }

  return `record_${index}`
}

/**
 * レコードキーをFirestoreのドキュメントIDとして使用可能な形式に変換
 */
function sanitizeRecordKey(key: string): string {
  return String(key).replace(/[/\s]/g, '_')
}

