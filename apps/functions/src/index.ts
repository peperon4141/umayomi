import { onRequest } from 'firebase-functions/v2/https'
import { logger } from 'firebase-functions'
import { initializeApp } from 'firebase-admin/app'
import * as path from 'path'
import * as fs from 'fs'
import { config } from 'dotenv'
import {
  handleScrapeJRACalendarWithRaceResults
} from './jra_scraper/handlers'
import { handleFetchJRDBDailyData, handleFetchJRDBAnnualData } from './jrdb_scraper/handlers'
import { handleRunDailyPrediction, handleRunPredictionWithDataFetch } from './prediction/handlers'
import { handleFetchJRDBDailyDataOnly } from './jrdb_scraper/handlers_fetch_only'
import { addYearMonthToRaces } from './utils/addYearMonthToRaces'
import { handleUploadModel } from './models/handlers'

// 開発環境の場合、.envファイルを読み込む
const isDevelopment = process.env.NODE_ENV === 'development' || 
                     process.env.FUNCTIONS_EMULATOR === 'true' ||
                     process.env.MODE === 'development'

if (isDevelopment) {
  // .envファイルを読み込む
  const envPath = path.join(process.cwd(), '.env')
  if (fs.existsSync(envPath)) {
    config({ path: envPath })
    logger.info('.envファイルを読み込みました', { envPath })
  } else logger.warn('.envファイルが見つかりません', { envPath })
  
}

if (isDevelopment) {
  // Firebase Admin SDKの環境変数を設定（initializeAppより前に設定）
  process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
  process.env.STORAGE_EMULATOR_HOST = '127.0.0.1:9198'
  logger.info('Firebase Emulator環境変数を設定しました', {
    firestoreEmulatorHost: process.env.FIRESTORE_EMULATOR_HOST,
    storageEmulatorHost: process.env.STORAGE_EMULATOR_HOST
  })
}

// Playwrightブラウザのパスを設定（実行時に必須）
// node_modules/playwright/.local-browsers を使用（Cloud Build/Cloud Runでpostinstallによりインストールされる）
if (!process.env.PLAYWRIGHT_BROWSERS_PATH) {
  const cwd = process.cwd()
  // Playwrightのデフォルトインストール先（node_modules配下）
  const defaultBrowserPath = path.join(cwd, 'node_modules', 'playwright', '.local-browsers')
  
  // ローカル開発環境の候補（workspace配下）
  const localWorkspacePath = path.resolve(cwd, '../../playwright-browsers')
  
  // 候補パスを順にチェック
  const candidatePaths = [
    defaultBrowserPath, // node_modules配下（Cloud Build/Cloud Run環境、postinstallでここにインストール）
    localWorkspacePath // ローカル開発環境（workspace配下）
  ]
  
  let foundPath: string | null = null
  for (const candidatePath of candidatePaths) 
    if (fs.existsSync(candidatePath)) {
      foundPath = candidatePath
      logger.info('Playwrightブラウザのパスを発見', {
        path: candidatePath,
        exists: true
      })
      break
    }
  
  
  if (foundPath) {
    process.env.PLAYWRIGHT_BROWSERS_PATH = foundPath
    logger.info('PLAYWRIGHT_BROWSERS_PATHを設定しました', {
      browsersPath: process.env.PLAYWRIGHT_BROWSERS_PATH
    })
  } else {
    // node_modules配下をデフォルトとして設定（postinstallでインストールされるはず）
    process.env.PLAYWRIGHT_BROWSERS_PATH = defaultBrowserPath
    logger.warn('Playwrightブラウザのパスが見つかりませんでした。デフォルトパスを設定しました', {
      browsersPath: process.env.PLAYWRIGHT_BROWSERS_PATH,
      warning: 'postinstallでブラウザがインストールされているか確認してください。'
    })
  }
} else 
  logger.info('PLAYWRIGHT_BROWSERS_PATHは既に設定されています', {
    browsersPath: process.env.PLAYWRIGHT_BROWSERS_PATH
  })


// Firebase Admin SDKを初期化
initializeApp()

/**
 * JRAカレンダーとレース結果データを一括取得・保存するCloud Function
 * 年と月を引数で受け取り、各日程のレース結果も含めて取得
 */
export const scrapeJRACalendarWithRaceResults = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleScrapeJRACalendarWithRaceResults
)

/**
 * JRDBから日単位で指定されたデータタイプを取得するCloud Function（デバッグ用）
 * 
 * 必須パラメータ（query）:
 * - year: 年（例: 2025）
 * - month: 月（例: 11）
 * - day: 日（例: 2）
 * - dataType: JRDBデータタイプ（例: BAC, HJC, TYB, UKC, OZ, OW, OU, OT, OV, JOA, ZED, ZEC, SED, SEC, KZA, KSA, CZA, CSA）または ALL（すべてのデータタイプを取得）
 * 
 * 例: 
 * - 単一データタイプ: https://.../fetchJRDBDailyData?year=2025&month=11&day=2&dataType=BAC
 * - すべてのデータタイプ: https://.../fetchJRDBDailyData?year=2025&month=11&day=2&dataType=ALL
 */
export const fetchJRDBDailyData = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleFetchJRDBDailyData
)

/**
 * JRDBから年度単位で指定されたデータタイプの年度パックを取得するCloud Function
 * 年度パックをサポートしているデータタイプのみ取得可能
 * 
 * 必須パラメータ（query）:
 * - year: 年度（例: 2024）
 * - dataType: JRDBデータタイプ（例: BAC, HJC, TYB, UKC, KYI, KYH, KYG, SED, SEC）または ALL（年度パックをサポートしているすべてのデータタイプを取得）
 * 
 * 例: 
 * - 単一データタイプ: https://.../fetchJRDBAnnualData?year=2024&dataType=TYB
 * - すべてのデータタイプ: https://.../fetchJRDBAnnualData?year=2024&dataType=ALL
 */
export const fetchJRDBAnnualData = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleFetchJRDBAnnualData
)

/**
 * Pythonスクリプトを実行してdailyデータを取得・分析・Firestoreに保存するCloud Function
 * 
 * 必須パラメータ（query）:
 * - modelStoragePath: Firebase Storage内のモデルパス（例: models/rank_model_202512111031_v1.txt）
 * 
 * オプショナルパラメータ（query）:
 * - date: 予測対象日付（YYYY-MM-DD形式、省略時は今日）
 * - useEmulator: Firebaseエミュレーターを使用するか（true/false、省略時はfalse）
 * 
 * 例: 
 * - 今日の予測: https://.../runDailyPrediction?modelStoragePath=models/rank_model_202512111031_v1.txt
 * - 指定日の予測: https://.../runDailyPrediction?modelStoragePath=models/rank_model_202512111031_v1.txt&date=2025-12-14
 * - エミュレーター使用: https://.../runDailyPrediction?modelStoragePath=models/rank_model_202512111031_v1.txt&useEmulator=true
 */
export const runDailyPrediction = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleRunDailyPrediction
)

/**
 * Pythonスクリプトを実行してJRDBからdailyデータを取得するCloud Function（データ取得のみ）
 * 
 * 必須パラメータ（query）:
 * - date: 日付（YYYY-MM-DD形式）または
 * - year, month, day: 年月日
 * 
 * 例: 
 * - 日付指定: https://.../fetchJRDBDailyDataOnly?date=2025-11-30
 * - 年月日指定: https://.../fetchJRDBDailyDataOnly?year=2025&month=11&day=30
 */
export const fetchJRDBDailyDataOnly = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleFetchJRDBDailyDataOnly
)

/**
 * 既存のracesコレクションのドキュメントにyearとmonthフィールドを追加するCloud Function
 */
/**
 * JRDBデータ取得と予測実行を統合したCloud Function
 * 
 * オプショナルパラメータ（query）:
 * - date: 予測対象日付（YYYY-MM-DD形式、省略時は今日）
 * - useEmulator: Firebaseエミュレーターを使用するか（true/false、省略時はfalse）
 * - autoSelectModel: 最新のモデルを自動選択するか（true/false、デフォルトはtrue）
 * 
 * 例: 
 * - 今日の予測（最新モデル使用）: https://.../runPredictionWithDataFetch
 * - 指定日の予測: https://.../runPredictionWithDataFetch?date=2025-12-14
 * - エミュレーター使用: https://.../runPredictionWithDataFetch?useEmulator=true
 */
export const runPredictionWithDataFetch = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleRunPredictionWithDataFetch
)

/**
 * 管理画面からモデルファイルをアップロードし、Firestore(models)にメタデータを保存するCloud Function
 *
 * 必須パラメータ（body JSON）:
 * - fileName: 元ファイル名（表示用）
 * - contentBase64: ファイル内容（base64）
 * - modelName: FirestoreのドキュメントID（例: rank_model_202512180040_v1）
 * - storagePath: Storage内のパス（例: models/rank_model_202512180040_v1.txt）
 *
 * オプショナル:
 * - version, description, trainingDate
 *
 * 認証:
 * - Authorization: Bearer <ID token> が必須
 * - 本番では role=admin を要求（エミュレータでは認証済みでOK）
 */
export const uploadModel = onRequest(
  { timeoutSeconds: 120, memory: '1GiB', region: 'asia-northeast1', cors: true },
  handleUploadModel
)

/**
 * 既存のracesコレクションのドキュメントにyearとmonthフィールドを追加するCloud Function
 */
export const addYearMonthToRacesCollection = onRequest(
  { timeoutSeconds: 600, memory: '1GiB', region: 'asia-northeast1', cors: true },
  async (request, response) => {
    try {
      await addYearMonthToRaces()
      response.status(200).send({
        success: true,
        message: 'yearとmonthフィールドの追加が完了しました'
      })
    } catch (error: any) {
      logger.error('yearとmonthフィールドの追加に失敗しました', { error })
      response.status(500).send({
        success: false,
        error: error.message
      })
    }
  }
)

