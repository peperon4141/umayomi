import { getFirestore, Timestamp } from 'firebase-admin/firestore'
import { logger } from 'firebase-functions'

// 遅延初期化でFirestoreインスタンスを取得
function getDb() {
  return getFirestore()
}

export interface FunctionLogData {
  functionName: string
  timestamp: Date
  year: string | undefined
  month: string | undefined
  success: boolean
  message: string
  error?: string
  executionTimeMs?: number
  additionalData?: Record<string, any>
}

/**
 * スクレイピング処理の結果をFirestoreのfunctions_logコレクションに保存
 */
export async function saveFunctionLog(logData: FunctionLogData): Promise<void> {
  try {
    const logDoc = {
      functionName: logData.functionName,
      timestamp: Timestamp.fromDate(logData.timestamp),
      year: logData.year,
      month: logData.month,
      success: logData.success,
      message: logData.message,
      error: logData.error,
      executionTimeMs: logData.executionTimeMs,
      createdAt: Timestamp.now(),
      // additionalDataをMap型で保存
      ...(logData.additionalData && Object.keys(logData.additionalData).length > 0 
        ? { additionalData: logData.additionalData } 
        : {})
    }

    await getDb().collection('functions_log').add(logDoc)
    
    logger.info('Function log saved to Firestore', {
      functionName: logData.functionName,
      year: logData.year,
      month: logData.month,
      success: logData.success,
      additionalDataKeys: logData.additionalData ? Object.keys(logData.additionalData) : []
    })
  } catch (error) {
    logger.error('Failed to save function log to Firestore', { error })
    // ログ保存の失敗は処理を停止させない
  }
}

/**
 * 成功時のログデータを作成
 */
export function createSuccessLog(
  functionName: string,
  year: string | undefined,
  month: string | undefined,
  message: string,
  additionalData: Record<string, any> = {}
): FunctionLogData {
  return {
    functionName,
    timestamp: new Date(),
    year,
    month,
    success: true,
    message,
    additionalData
  }
}

/**
 * エラー時のログデータを作成
 */
export function createErrorLog(
  functionName: string,
  year: string | undefined,
  month: string | undefined,
  error: string,
  additionalData: Record<string, any> = {}
): FunctionLogData {
  return {
    functionName,
    timestamp: new Date(),
    year,
    month,
    success: false,
    message: 'スクレイピング処理でエラーが発生しました',
    error,
    additionalData
  }
}
