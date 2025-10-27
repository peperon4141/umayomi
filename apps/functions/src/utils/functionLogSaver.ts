import { getFirestore, Timestamp } from 'firebase-admin/firestore'
import { logger } from 'firebase-functions'

// Firestoreインスタンスをキャッシュ
// let dbInstance: FirebaseFirestore.Firestore | null = null

// 遅延初期化でFirestoreインスタンスを取得
// function getDb() {
//   if (!dbInstance) {
//     // 開発環境でFirestore Emulatorに接続
//     const isDevelopment = process.env.NODE_ENV === 'development' || 
//                          process.env.FUNCTIONS_EMULATOR === 'true' ||
//                          process.env.MODE === 'development'
    
//     // if (isDevelopment) {
//     //   // Firebase Admin SDKの環境変数を設定（getFirestoreより前に設定）
//     //   process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
//     //   logger.info('Firestore Emulator環境変数を設定しました', {
//     //     firestoreEmulatorHost: process.env.FIRESTORE_EMULATOR_HOST,
//     //     nodeEnv: process.env.NODE_ENV,
//     //     functionsEmulator: process.env.FUNCTIONS_EMULATOR,
//     //     mode: process.env.MODE
//     //   })
//     // }
    
//     dbInstance = getFirestore()
    
//     if (isDevelopment && !process.env.FIRESTORE_EMULATOR_HOST) {
//       logger.warn('Firestore Emulator環境変数が設定されていません')
//     }
//   }
  
//   return dbInstance
// }

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
      // undefinedの場合はフィールドを除外
      ...(logData.error && { error: logData.error }),
      ...(logData.executionTimeMs && { executionTimeMs: logData.executionTimeMs }),
      createdAt: Timestamp.now(),
      // additionalDataをMap型で保存
      ...(logData.additionalData && Object.keys(logData.additionalData).length > 0 
        ? { additionalData: logData.additionalData } 
        : {})
    }

    const db = getFirestore()
    const docRef = await db.collection('functions_log').add(logDoc)
    
    logger.info('Function log saved to Firestore', {
      functionName: logData.functionName,
      year: logData.year,
      month: logData.month,
      success: logData.success,
      additionalDataKeys: logData.additionalData ? Object.keys(logData.additionalData) : [],
      docId: docRef.id,
      firestoreEmulatorHost: process.env.FIRESTORE_EMULATOR_HOST
    })
  } catch (error) {
    logger.error('Failed to save function log to Firestore', { 
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined,
      firestoreEmulatorHost: process.env.FIRESTORE_EMULATOR_HOST
    })
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
