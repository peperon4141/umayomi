import { downloadFileAsBuffer } from '../../downloader'
import { getJRDBDataTypeInfo } from '../../entities/jrdb'
import type { JRDBDataType } from '../../entities/jrdb'

// loggerは条件付きで使用（スクリプト実行時は未定義の可能性がある）
function getLogger() {
  try {
     
    const { logger } = require('firebase-functions')
    return logger
  } catch {
    // スクリプト実行時はloggerが使えない場合がある
    return {
      info: (message: string, meta?: Record<string, unknown>) => console.log(`[INFO] ${message}`, meta || ''),
      warn: (message: string, meta?: Record<string, unknown>) => console.warn(`[WARN] ${message}`, meta || '')
    }
  }
}

/**
 * メンバーページのHTMLを取得
 */
export async function fetchMemberIndexHtml(dataType: JRDBDataType): Promise<string> {
  const info = getJRDBDataTypeInfo(dataType)
  const url = `${info.dataFileBaseUrl}/index.html`
  getLogger().info('Fetching member index page', { dataType, url })
  
  const buffer = await downloadFileAsBuffer(url, {
    username: process.env.JRDB_USERNAME,
    password: process.env.JRDB_PASSWORD
  })
  
  // JRDBのHTMLはShift-JISでエンコードされている
  const iconv = await import('iconv-lite')
  return iconv.default.decode(buffer, 'shift_jis')
}

/**
 * HTMLから年度パックが提供されているか判定
 * 年度パック形式のファイル名（例: TYB_2024.lzh）を検索
 */
function hasAnnualPackInHtml(html: string, dataType: string): boolean {
  const upperDataType = dataType.toUpperCase()
  
  // 年度パック形式のファイル名を検索（例: TYB_2024.lzh, TYB_2023.lzh）
  // パターン: {データタイプ}_YYYY.lzh または {データタイプ}_YY.lzh
  const annualPackPattern = new RegExp(`${upperDataType}_\\d{4}\\.lzh`, 'i')
  if (annualPackPattern.test(html)) {
    getLogger().info('年度パック形式のファイル名を検出', { dataType, pattern: annualPackPattern.source })
    return true
  }
  
  // 年度パック関連のキーワードを検索
  const annualPackKeywords = [
    '年度パック',
    '年度版',
    '年度コーナー',
    '年度ごと'
  ]
  
  for (const keyword of annualPackKeywords) 
    if (html.includes(keyword)) {
      getLogger().info('年度パック関連のキーワードを検出', { dataType, keyword })
      return true
    }
  
  
  return false
}

/**
 * データタイプに年度パックが提供されているか判定
 * メンバーページのindex.htmlにアクセスして確認
 */
export async function checkAnnualPackAvailability(dataType: JRDBDataType): Promise<boolean> {
  try {
    const html = await fetchMemberIndexHtml(dataType)
    return hasAnnualPackInHtml(html, dataType)
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    getLogger().warn('年度パックの判定に失敗しました', { dataType, error: errorMessage })
    // エラー時はfalseを返す（年度パックなしとみなす）
    return false
  }
}

/**
 * 複数のデータタイプの年度パック提供状況を一括確認
 */
export async function checkAnnualPackAvailabilityBatch(
  dataTypes: JRDBDataType[]
): Promise<Record<JRDBDataType, boolean>> {
  const results: Record<JRDBDataType, boolean> = {} as Record<JRDBDataType, boolean>
  
  for (const dataType of dataTypes) 
    results[dataType] = await checkAnnualPackAvailability(dataType)
  
  return results
}

