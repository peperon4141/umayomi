// Firebase Admin SDKのTimestamp型を使用
// 実際の使用時はfirebase-admin/firestoreからimport

/**
 * Cloud Functions実行ログの型定義
 */
export interface FunctionLog {
  /** ドキュメントID */
  id: string
  /** 関数名 */
  functionName: string
  /** 実行ステータス */
  status: 'success' | 'failure'
  /** 実行日時 */
  executedAt: any // Firestore Timestamp型
  /** 追加情報（オプション） */
  metadata?: {
    /** 実行時間（ミリ秒） */
    duration?: number
    /** エラーメッセージ（失敗時） */
    errorMessage?: string
    /** レスポンスデータ（成功時） */
    responseData?: any
    /** リクエストメソッド */
    method?: string
    /** リクエストURL */
    url?: string
    /** その他のカスタムデータ */
    [key: string]: any
  }
}

/**
 * FunctionLog作成用のヘルパー型
 */
export interface CreateFunctionLogData {
  functionName: string
  status: 'success' | 'failure'
  metadata?: FunctionLog['metadata']
}
