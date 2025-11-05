import { initializeApp, getApps } from 'firebase-admin/app'
import { getAuth } from 'firebase-admin/auth'

// Firebase Emulator用の環境変数を設定
process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
process.env.FIREBASE_AUTH_EMULATOR_HOST = '127.0.0.1:9199'
process.env.GCLOUD_PROJECT = 'umayomi-fbb2b'

// Firebase Admin SDKの初期化
if (!getApps().length) {
  initializeApp({
    projectId: 'umayomi-fbb2b',
    // Firebase Emulatorを使用するため、認証情報は不要
  })
}

const auth = getAuth()

/**
 * テスト用ユーザーを作成する
 * 既に存在する場合は何もしない
 */
export async function ensureTestUser(email: string, password: string): Promise<void> {
  try {
    // 既存ユーザーを確認
    try {
      await auth.getUserByEmail(email)
      // ユーザーが存在する場合は何もしない
      return
    } catch (error: unknown) {
      // ユーザーが存在しない場合は作成
      if (error && typeof error === 'object' && 'code' in error && error.code === 'auth/user-not-found') {
        await auth.createUser({
          email,
          password,
          emailVerified: true,
        })
      } else {
        throw error
      }
    }
  } catch (error: unknown) {
    // エラーが発生した場合はログ出力して続行
    const errorMessage = error && typeof error === 'object' && 'message' in error && typeof error.message === 'string'
      ? error.message
      : String(error)
    // eslint-disable-next-line no-console
    console.warn(`Failed to create test user ${email}:`, errorMessage)
  }
}
