import { getStorage } from 'firebase-admin/storage'
import { Storage } from '@google-cloud/storage'
import { logger } from 'firebase-functions'
import * as fs from 'fs'
import * as path from 'path'

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
  
  let bucket: any
  if (isDevelopment) {
    const storage = new Storage({
      apiEndpoint: `http://${storageEmulatorHost}`,
      projectId: 'umayomi-fbb2b'
    })
    bucket = storage.bucket('umayomi-fbb2b.firebasestorage.app')
  } else 
    bucket = getStorage().bucket()
  

  try {
    const uploadOptions: {
      destination: string
      metadata: {
        contentType: string
        metadata?: Record<string, string>
      }
    } = {
      destination: storagePath,
      metadata: {
        contentType: 'application/octet-stream'
      }
    }
    
    if (metadata && Object.keys(metadata).length > 0) uploadOptions.metadata.metadata = metadata

    await bucket.upload(localFilePath, uploadOptions)

    if (metadata && Object.keys(metadata).length > 0) 
      try {
        const file = bucket.file(storagePath)
        await file.setMetadata({ metadata })
      } catch (metadataError) {
        logger.warn('メタデータの更新に失敗しました', {
          error: metadataError instanceof Error ? metadataError.message : String(metadataError),
          storagePath
        })
      }
    

    logger.info('Storageにファイルをアップロードしました', {
      storagePath,
      localFilePath,
      isDevelopment,
      customMetadata: metadata
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
 * 一時ディレクトリを削除
 */
export function cleanupTempDir(dirPath: string): void {
  try {
    if (fs.existsSync(dirPath)) {
      fs.rmSync(dirPath, { recursive: true, force: true })
      logger.info('一時ディレクトリを削除しました', { dirPath })
    }
  } catch (error) {
    logger.warn('一時ディレクトリの削除に失敗しました', {
      error: error instanceof Error ? error.message : String(error),
      dirPath
    })
  }
}

/**
 * 一時ディレクトリを作成
 */
export function createTempDir(): string {
  const tempDir = path.join(process.cwd(), 'temp')
  if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true })
  
  return tempDir
}

