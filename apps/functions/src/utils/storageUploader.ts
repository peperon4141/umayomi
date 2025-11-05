import { getStorage } from 'firebase-admin/storage'
import { Storage } from '@google-cloud/storage'
import { logger } from 'firebase-functions'
import * as fs from 'fs'
import * as path from 'path'
import { JRDBDataType } from '../../../shared/src/jrdb'

/**
 * Firebase Storageにファイルをアップロード
 */
export async function uploadFileToStorage(
  localFilePath: string,
  storagePath: string,
  metadata?: Record<string, string>
): Promise<void> {
  // 開発環境の場合、STORAGE_EMULATOR_HOSTを確認
  const isDevelopment = process.env.NODE_ENV === 'development' || 
                       process.env.FUNCTIONS_EMULATOR === 'true' ||
                       process.env.MODE === 'development'
  
  const storageEmulatorHost = process.env.STORAGE_EMULATOR_HOST || '127.0.0.1:9198'
  
  logger.info('Storage接続設定', {
    storageEmulatorHost,
    isDevelopment
  })
  
  // 開発環境では、@google-cloud/storageを直接使用してStorage Emulatorに接続
  let bucket: any
  if (isDevelopment) {
    const storage = new Storage({
      apiEndpoint: `http://${storageEmulatorHost}`,
      projectId: 'umayomi-fbb2b'
    })
    bucket = storage.bucket('umayomi-fbb2b.firebasestorage.app')
  } else {
    bucket = getStorage().bucket()
  }
  
  try {
    await bucket.upload(localFilePath, {
      destination: storagePath,
      metadata: {
        contentType: 'application/octet-stream',
        metadata: metadata || {}
      }
    })

    logger.info('Storageにファイルをアップロードしました', {
      storagePath,
      localFilePath,
      isDevelopment
    })
  } catch (error) {
    logger.error('Storageへのアップロードに失敗しました', {
      error: error instanceof Error ? error.message : String(error),
      storagePath,
      localFilePath,
      isDevelopment,
      storageEmulatorHost
    })
    throw error
  }
}

/**
 * JRDBデータのParquetファイルをStorageにアップロード
 * ファイル名ベースで保存する場合
 */
export async function uploadJRDBParquetToStorageWithFileName(
  localFilePath: string,
  fileName: string
): Promise<string> {
  const storagePath = `jrdb_data/${fileName}.parquet`
  
  const metadata: Record<string, string> = {
    fileName,
    uploadedAt: new Date().toISOString()
  }

  await uploadFileToStorage(localFilePath, storagePath, metadata)

  return storagePath
}

/**
 * JRDBデータのParquetファイルをStorageにアップロード（データ種別・年ベース）
 * @deprecated ファイル名ベースの保存を推奨
 */
export async function uploadJRDBParquetToStorage(
  localFilePath: string,
  dataType: JRDBDataType,
  year: number
): Promise<string> {
  const storagePath = `jrdb_data/${dataType}/${dataType}_${year}.parquet`
  
  const metadata: Record<string, string> = {
    dataType,
    year: year.toString(),
    uploadedAt: new Date().toISOString()
  }

  await uploadFileToStorage(localFilePath, storagePath, metadata)

  return storagePath
}

/**
 * 一時ファイルを削除
 */
export function cleanupTempFile(filePath: string): void {
  try {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath)
      logger.info('一時ファイルを削除しました', { filePath })
    }
  } catch (error) {
    logger.warn('一時ファイルの削除に失敗しました', {
      error: error instanceof Error ? error.message : String(error),
      filePath
    })
  }
}

/**
 * 一時ディレクトリを作成
 */
export function createTempDir(): string {
  const tempDir = path.join(process.cwd(), 'temp')
  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true })
  }
  return tempDir
}

