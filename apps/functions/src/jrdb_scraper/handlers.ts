import { logger } from 'firebase-functions'
import * as path from 'path'
import * as fs from 'fs'
import { convertLzhToParquet } from './converter'
import { uploadJRDBParquetToStorageWithFileName, createTempDir, cleanupTempFile } from '../utils/storageUploader'
import { downloadJRDBFile, extractFileNameFromUrl, extractBaseFileNameFromUrl, parseFileName } from './downloader'
import { JRDBDataType } from '../../../shared/src/jrdb'
import { fetchRaceKYData } from './fetchRaceKYData'
import { fetchDailyKYIData } from './fetchDailyKYIData'

/**
 * Request型（Firebase FunctionsのRequest型の簡易版）
 */
interface Request {
  query?: {
    url?: string
    dataType?: string
    year?: string
    month?: string
    day?: string
    racecourse?: string
    kaisaiRound?: string
    kaisaiDay?: string
    raceNumber?: string
  }
  body?: {
    url?: string
    dataType?: string
    year?: string
    file?: Buffer | string
  }
}

/**
 * Response型（Firebase FunctionsのResponse型の簡易版）
 */
interface Response {
  // eslint-disable-next-line no-unused-vars
  status: (code: number) => Response
  // eslint-disable-next-line no-unused-vars
  send: (data: unknown) => void
}

/**
 * JRDBデータをlzh形式からParquet形式に変換してFirebase Storageに保存する処理
 * URLからダウンロードする場合と、ファイルを直接アップロードする場合の両方に対応
 */
export async function handleConvertJRDBToParquet(request: Request, response: Response): Promise<void> {
  const startTime = Date.now()
  logger.info('JRDB to Parquet conversion function called')

  try {
    const url = request.query?.url || request.body?.url
    const dataType = request.query?.dataType || request.body?.dataType
    const year = request.query?.year || request.body?.year
    const lzhFile = request.body?.file

    let lzhBuffer: Buffer
    let targetDataType: JRDBDataType | null
    let targetYear: number
    let baseFileName: string | null = null

    // URLからダウンロードする場合
    if (url) {
      logger.info('Downloading JRDB file from URL', { url })
      lzhBuffer = await downloadJRDBFile(url)
      
      // ファイル名（拡張子を除く）を抽出（例: JRDB251102）
      baseFileName = extractBaseFileNameFromUrl(url)
      logger.info('Extracted base file name from URL', { baseFileName })
      
      // ファイル名からデータ種別と年を推測
      const fileName = extractFileNameFromUrl(url)
      const parsed = parseFileName(fileName)
      
      targetDataType = (dataType ? (dataType as JRDBDataType) : null) || (parsed.dataType ? (parsed.dataType as JRDBDataType) : null) || null
      targetYear = year ? parseInt(year as string) : (parsed.year || new Date().getFullYear())
    } 
    // ファイルを直接アップロードする場合
    else if (lzhFile) {
      if (!dataType || !year) {
        const errorMessage = 'dataType and year parameters are required when uploading file directly'
        logger.error(errorMessage)
        response.status(400).send({ success: false, error: errorMessage })
        return
      }

      // lzhファイルをBufferに変換
      if (Buffer.isBuffer(lzhFile)) {
        lzhBuffer = lzhFile
      } else if (typeof lzhFile === 'string') {
        lzhBuffer = Buffer.from(lzhFile, 'base64')
      } else {
        throw new Error('Invalid file format')
      }

      targetDataType = dataType as JRDBDataType
      targetYear = parseInt(year as string)
    } else {
      const errorMessage = 'Either url or file parameter is required'
      logger.error(errorMessage)
      response.status(400).send({ success: false, error: errorMessage })
      return
    }

    // 一時ディレクトリを作成
    const tempDir = createTempDir()
    const tempDataType = targetDataType || 'UNKNOWN'
    const tempParquetPath = path.join(tempDir, `${tempDataType}_${targetYear}.parquet`)

    let finalDataType: JRDBDataType
    let finalParquetPath: string = tempParquetPath

    try {
      // lzhファイルをParquetに変換（実際のデータ種別を取得）
      const { actualDataType } = await convertLzhToParquet(lzhBuffer, targetDataType, targetYear, tempParquetPath)
      
      // 実際のデータ種別を使用してStorageにアップロード
      finalDataType = actualDataType
      finalParquetPath = path.join(tempDir, `${finalDataType}_${targetYear}.parquet`)
      
      // ファイルが正しく作成されているか確認
      if (!fs.existsSync(tempParquetPath)) {
        logger.error('Parquetファイルが作成されていません', {
          tempParquetPath,
          tempDir,
          dirExists: fs.existsSync(tempDir),
          filesInDir: fs.existsSync(tempDir) ? fs.readdirSync(tempDir) : []
        })
        throw new Error(`Parquet file was not created: ${tempParquetPath}`)
      }
      
      logger.info('Parquetファイル作成確認', {
        tempParquetPath,
        tempParquetExists: fs.existsSync(tempParquetPath),
        finalParquetPath,
        targetDataType,
        actualDataType: finalDataType
      })
      
      // データ種別が変更された場合、またはtargetDataTypeがnullの場合はファイル名を変更
      // tempParquetPathとfinalParquetPathが異なる場合のみリネーム
      if (tempParquetPath !== finalParquetPath) {
        logger.info('ファイル名変更が必要です', {
          targetDataType,
          finalDataType,
          tempParquetPath,
          finalParquetPath,
          tempParquetExists: fs.existsSync(tempParquetPath),
          finalParquetExists: fs.existsSync(finalParquetPath)
        })
        
        if (fs.existsSync(tempParquetPath)) {
          // ファイルが存在する場合のみリネーム
          try {
            // リネーム先のファイルが既に存在する場合は削除
            if (fs.existsSync(finalParquetPath)) {
              fs.unlinkSync(finalParquetPath)
              logger.info('既存のファイルを削除しました', { finalParquetPath })
            }
            
            fs.renameSync(tempParquetPath, finalParquetPath)
            logger.info('Parquetファイル名を変更しました', { 
              oldPath: tempParquetPath, 
              newPath: finalParquetPath, 
              oldDataType: targetDataType || 'UNKNOWN', 
              newDataType: finalDataType 
            })
          } catch (renameError) {
            logger.error('ファイル名変更に失敗しました', {
              error: renameError instanceof Error ? renameError.message : String(renameError),
              tempParquetPath,
              finalParquetPath,
              tempParquetExists: fs.existsSync(tempParquetPath),
              finalParquetExists: fs.existsSync(finalParquetPath),
              tempDir,
              filesInDir: fs.existsSync(tempDir) ? fs.readdirSync(tempDir) : []
            })
            throw renameError
          }
        } else {
          // ファイルが存在しない場合、finalParquetPathが正しいパスか確認
          logger.warn('Parquetファイルが見つかりません', {
            tempParquetPath,
            finalParquetPath,
            tempParquetExists: fs.existsSync(tempParquetPath),
            finalParquetExists: fs.existsSync(finalParquetPath),
            tempDir,
            filesInDir: fs.existsSync(tempDir) ? fs.readdirSync(tempDir) : []
          })
          // finalParquetPathが存在しない場合はエラー
          if (!fs.existsSync(finalParquetPath)) {
            throw new Error(`Parquet file not found: ${tempParquetPath} or ${finalParquetPath}`)
          }
        }
      } else {
        // ファイル名変更が不要な場合
        logger.info('ファイル名変更は不要です', {
          targetDataType,
          finalDataType,
          finalParquetPath
        })
      }
      
      // 最終的に使用するファイルパスを確認
      if (!fs.existsSync(finalParquetPath)) {
        logger.error('最終的なParquetファイルが見つかりません', {
          finalParquetPath,
          tempParquetPath,
          tempParquetExists: fs.existsSync(tempParquetPath),
          finalParquetExists: fs.existsSync(finalParquetPath),
          tempDir,
          filesInDir: fs.existsSync(tempDir) ? fs.readdirSync(tempDir) : []
        })
        throw new Error(`Final Parquet file not found: ${finalParquetPath}`)
      }
      
      logger.info('最終的なParquetファイルパスを確認', {
        finalParquetPath,
        fileSize: fs.statSync(finalParquetPath).size
      })

      // ParquetファイルをStorageにアップロード
      // URLから取得したファイル名を使用する場合
      let storagePath: string
      if (baseFileName) {
        storagePath = await uploadJRDBParquetToStorageWithFileName(
          finalParquetPath,
          baseFileName
        )
      } else {
        // ファイル直接アップロードの場合は従来通り
        const { uploadJRDBParquetToStorage } = await import('../utils/storageUploader')
        storagePath = await uploadJRDBParquetToStorage(
          finalParquetPath,
          finalDataType,
          targetYear
        )
      }

      const executionTimeMs = Date.now() - startTime
      const message = baseFileName 
        ? `${baseFileName}のParquet変換・保存が完了しました`
        : `${finalDataType}データ（${targetYear}年）のParquet変換・保存が完了しました`

      response.send({
        success: true,
        message,
        dataType: finalDataType,
        originalDataType: targetDataType !== finalDataType ? targetDataType : undefined,
        year: targetYear,
        fileName: baseFileName || undefined,
        storagePath,
        executionTimeMs
      })
    } finally {
      // 一時ファイルを削除
      cleanupTempFile(tempParquetPath)
      if (finalParquetPath !== tempParquetPath) {
        cleanupTempFile(finalParquetPath)
      }
    }

  } catch (error) {
    const executionTimeMs = Date.now() - startTime
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('JRDB to Parquet conversion failed', {
      errorMessage,
      errorStack,
      executionTimeMs
    })

    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

/**
 * 特定レースのKY系データをすべて取得する処理
 * 2025-11-02 東京 11レースをサンプルとして実装
 */
export async function handleFetchRaceKYData(request: Request, response: Response): Promise<void> {
  const startTime = Date.now()
  logger.info('Fetch race KY data function called')

  try {
    // リクエストパラメータからレース情報を取得（queryパラメータのみ、必須）
    if (!request.query?.year || !request.query?.month || !request.query?.day || !request.query?.racecourse || !request.query?.raceNumber) {
      const errorMessage = 'year, month, day, racecourse, raceNumber parameters are required'
      logger.error(errorMessage)
      response.status(400).send({ success: false, error: errorMessage })
      return
    }

    const year = parseInt(String(request.query.year))
    const month = parseInt(String(request.query.month))
    const day = parseInt(String(request.query.day))
    const racecourse = request.query.racecourse as string
    const raceNumber = parseInt(String(request.query.raceNumber))
    
    // 開催回数と日目はオプショナル（デフォルト値なし、未指定の場合はエラー）
    if (!request.query?.kaisaiRound || !request.query?.kaisaiDay) {
      const errorMessage = 'kaisaiRound and kaisaiDay parameters are required'
      logger.error(errorMessage)
      response.status(400).send({ success: false, error: errorMessage })
      return
    }

    const kaisaiRound = parseInt(String(request.query.kaisaiRound))
    const kaisaiDay = parseInt(String(request.query.kaisaiDay))

    logger.info('Fetching KY data for race', {
      year,
      month,
      day,
      racecourse,
      kaisaiRound,
      kaisaiDay,
      raceNumber
    })

    // KY系データを取得
    const result = await fetchRaceKYData(
      year,
      month,
      day,
      racecourse,
      kaisaiRound,
      kaisaiDay,
      raceNumber
    )

    const executionTimeMs = Date.now() - startTime

    response.send({
      success: true,
      message: `KY系データの取得が完了しました（レースキー: ${result.raceKey}）`,
      raceKey: result.raceKey,
      dataTypes: result.dataTypes,
      results: result.results,
      executionTimeMs
    })

  } catch (error) {
    const executionTimeMs = Date.now() - startTime
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('Fetch race KY data failed', {
      errorMessage,
      errorStack,
      executionTimeMs
    })

    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

/**
 * 日単位でKYIデータを取得する処理
 * 2025-11-02をサンプルとして実装
 */
export async function handleFetchDailyKYIData(request: Request, response: Response): Promise<void> {
  const startTime = Date.now()
  logger.info('Fetch daily KYI data function called')

  try {
    // リクエストパラメータから日付情報を取得（queryパラメータのみ、必須）
    if (!request.query?.year || !request.query?.month || !request.query?.day) {
      const errorMessage = 'year, month, day parameters are required'
      logger.error(errorMessage)
      response.status(400).send({ success: false, error: errorMessage })
      return
    }

    const year = parseInt(String(request.query.year))
    const month = parseInt(String(request.query.month))
    const day = parseInt(String(request.query.day))

    logger.info('Fetching KYI data for date', {
      year,
      month,
      day
    })

    // KYIデータを取得
    const result = await fetchDailyKYIData(year, month, day)

    const executionTimeMs = Date.now() - startTime

    if (result.success) {
      response.send({
        success: true,
        message: `KYIデータの取得が完了しました（日付: ${result.date}）`,
        date: result.date,
        recordCount: result.recordCount,
        storagePath: result.storagePath,
        fileName: result.fileName,
        executionTimeMs
      })
    } else {
      response.status(500).send({
        success: false,
        error: result.error,
        date: result.date,
        executionTimeMs
      })
    }

  } catch (error) {
    const executionTimeMs = Date.now() - startTime
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('Fetch daily KYI data failed', {
      errorMessage,
      errorStack,
      executionTimeMs
    })

    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}
