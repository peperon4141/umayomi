import { onRequest } from 'firebase-functions/v2/https'
import { logger } from 'firebase-functions'
import { initializeApp } from 'firebase-admin/app'
import * as path from 'path'
import * as fs from 'fs'
import { config } from 'dotenv'
import {
  handleScrapeJRACalendarWithRaceResults
} from './jra_scraper/handlers'
import { handleConvertJRDBToParquet } from './jrdb_scraper/handlers'

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
  } else {
    logger.warn('.envファイルが見つかりません', { envPath })
  }
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
  for (const candidatePath of candidatePaths) {
    if (fs.existsSync(candidatePath)) {
      foundPath = candidatePath
      logger.info('Playwrightブラウザのパスを発見', {
        path: candidatePath,
        exists: true
      })
      break
    }
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
} else {
  logger.info('PLAYWRIGHT_BROWSERS_PATHは既に設定されています', {
    browsersPath: process.env.PLAYWRIGHT_BROWSERS_PATH
  })
}

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
 * JRDBデータをlzh形式からParquet形式に変換してFirebase Storageに保存するCloud Function
 * lzhファイルをアップロードしてParquetに変換し、Storageに保存
 */
export const convertJRDBToParquet = onRequest(
  { timeoutSeconds: 600, memory: '2GiB', region: 'asia-northeast1', cors: true },
  handleConvertJRDBToParquet
)
