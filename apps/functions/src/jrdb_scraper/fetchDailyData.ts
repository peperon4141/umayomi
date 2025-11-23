import { logger } from 'firebase-functions'
import { downloadJRDBFile } from './downloader'
import { convertLzhToNpz } from './converter'
import { generateJRDBDataFileUrl } from './raceKeyGenerator'
import { getFirestore } from 'firebase-admin/firestore'
import { JRDBDataType } from './entities/jrdb'
import * as path from 'path'
import * as fs from 'fs'
import { createTempDir, uploadFileToStorage } from '../utils/storageUploader'
import { createDateFromYMD, formatDateISO, formatDateJRDB } from './utils/dateFormatter'
import { createStorageMetadata, createFirestoreMetadata } from './utils/metadata'
import { generateRecordKey } from './utils/recordKey'


/**
 * 単一のデータタイプのデータを取得してFirestoreに保存（内部関数）
 */
async function fetchSingleDataType(
  year: number,
  month: number,
  day: number,
  dataType: JRDBDataType,
  date: string
): Promise<{
  date: string
  dataType: string
  success: boolean
  recordCount: number
  lzhStoragePath?: string
  npzStoragePath?: string
  jsonStoragePath?: string
  fileName?: string
  error?: string
}> {
  logger.info('日単位データ取得開始', { date, dataType })

  const db = getFirestore()
  const tempDir = createTempDir()

  try {
    const actualDataType = dataType.toString()
    const dateObj = createDateFromYMD(year, month, day)
    const dateStr = formatDateJRDB(year, month, day)
    const sourceUrl = generateJRDBDataFileUrl(actualDataType, dateObj)
    const lzhBuffer = await downloadJRDBFile(sourceUrl)
    const fileName = `${actualDataType}${dateStr}`
    const npzFilePath = path.join(tempDir, `${fileName}.npz`)
    const { records } = await convertLzhToNpz(lzhBuffer, actualDataType, year, npzFilePath)

    if (records.length === 0) throw new Error('パースされたレコードが0件です')

    // 3. LZHファイル、NPZファイル、JSONファイルをStorageに保存
    
    // 3-1. LZHファイルをStorageに保存
    const lzhFilePath = path.join(tempDir, `${fileName}.lzh`)
    fs.writeFileSync(lzhFilePath, lzhBuffer)
    const lzhStoragePath = `jrdb/lzh/${fileName}.lzh`
    const lzhMetadata = createStorageMetadata(fileName, sourceUrl, actualDataType, date)
    let lzhStoragePathResult: string | undefined = lzhStoragePath
    try {
      await uploadFileToStorage(lzhFilePath, lzhStoragePath, lzhMetadata)
      logger.info('LZHファイルをStorageに保存しました', { lzhStoragePath, fileName, sourceUrl })
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      logger.error('LZHファイルのStorageへの保存に失敗しました', { fileName, error: errorMessage })
      // LZHファイルの保存失敗はエラーとしない（NPZファイルがあれば問題ない）
      lzhStoragePathResult = undefined
    }

    // 3-2. NPZファイルをStorageにアップロード
    if (!fs.existsSync(npzFilePath)) throw new Error(`NPZファイルが存在しません: ${npzFilePath}`)
    
    const npzStoragePath = `jrdb/npz/${fileName}.npz`
    const npzMetadata = createStorageMetadata(fileName, sourceUrl, actualDataType, date)
    await uploadFileToStorage(npzFilePath, npzStoragePath, npzMetadata)
    
    logger.info('NPZファイルをStorageに保存しました', { storagePath: npzStoragePath, fileName, sourceUrl })

    // 3-3. JSONファイルをStorageにアップロード
    const { convertToJson } = await import('./converter')
    const jsonFilePath = path.join(tempDir, `${fileName}.json`)
    await convertToJson(records, jsonFilePath)
    
    const jsonStoragePath = `jrdb/json/${fileName}.json`
    const jsonMetadata = createStorageMetadata(fileName, sourceUrl, actualDataType, date)
    await uploadFileToStorage(jsonFilePath, jsonStoragePath, jsonMetadata)
    
    logger.info('JSONファイルをStorageに保存しました', { storagePath: jsonStoragePath, fileName, sourceUrl })

    // 4. Firestoreにメタデータとパースしたデータを保存
    // すべてのレコードをコレクションとして統一して保存する
    const dailyDocRef = db.collection('jrdb_daily_data').doc(date)
    const dataTypeRef = dailyDocRef.collection(actualDataType.toString()).doc('metadata')

    const metadataToSave = createFirestoreMetadata(
      actualDataType,
      date,
      year,
      month,
      day,
      lzhStoragePathResult,
      npzStoragePath,
      jsonStoragePath,
      fileName,
      records.length
    )
    
    if (actualDataType !== dataType.toString()) metadataToSave.originalDataType = dataType.toString()
    
    
    await dataTypeRef.set(metadataToSave, { merge: true })

    // 各レコードを個別のドキュメントとしてサブコレクションに保存
    const recordsCollection = dailyDocRef.collection(actualDataType.toString()).doc('metadata').collection('records')
    let batch = db.batch()
    let batchCount = 0
    const maxBatchSize = 500

    for (let i = 0; i < records.length; i++) {
      const record = records[i]
      const recordKey = generateRecordKey(record, i)
      const recordRef = recordsCollection.doc(recordKey)
      batch.set(recordRef, {
        ...record,
        index: i
      })
      batchCount++

      if (batchCount >= maxBatchSize) {
        await batch.commit()
        batch = db.batch() // 新しいbatchを作成
        batchCount = 0
      }
    }

    if (batchCount > 0) await batch.commit()
    

    logger.info('レコードをコレクションとして保存しました', {
      dataType: actualDataType,
      date,
      totalRecords: records.length
    })

    // 5. 日単位のメタデータを保存
    await dailyDocRef.set({
      date,
      year,
      month,
      day,
      fetchedAt: new Date()
    }, { merge: true })

    return {
      date,
      dataType: actualDataType.toString(),
      success: true,
      recordCount: records.length,
      lzhStoragePath: lzhStoragePathResult,
      npzStoragePath: npzStoragePath,
      jsonStoragePath: jsonStoragePath,
      fileName
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    logger.error('日単位データ取得エラー', { date, dataType, error: errorMessage })

    return {
      date,
      dataType: dataType.toString(),
      success: false,
      recordCount: 0,
      error: errorMessage
    }
  } finally {
    try {
      fs.rmSync(tempDir, { recursive: true, force: true })
    } catch {
      // クリーンアップエラーは無視
    }
  }
}

/**
 * 日単位で指定されたデータタイプのデータを取得してFirestoreに保存
 * @param year - 年
 * @param month - 月
 * @param day - 日
 * @param dataTypes - データタイプの配列
 */
export async function fetchDailyData(
  year: number,
  month: number,
  day: number,
  dataTypes: JRDBDataType[]
): Promise<Array<{
  date: string
  dataType: string
  success: boolean
  recordCount: number
  lzhStoragePath?: string
  npzStoragePath?: string
  jsonStoragePath?: string
  fileName?: string
  error?: string
  }>> {
  const date = formatDateISO(year, month, day)

  logger.info('日単位データ取得開始（複数データタイプ）', { date, dataTypes: dataTypes.map(dt => dt.toString()) })

  const results: Array<{
    date: string
    dataType: string
    success: boolean
    recordCount: number
    lzhStoragePath?: string
    npzStoragePath?: string
    jsonStoragePath?: string
    fileName?: string
    error?: string
  }> = []

  for (const dataType of dataTypes) 
    try {
      const result = await fetchSingleDataType(year, month, day, dataType, date)
      results.push(result)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error)
      logger.error('データタイプ取得エラー', { date, dataType, error: errorMessage })
      results.push({
        date,
        dataType: dataType.toString(),
        success: false,
        recordCount: 0,
        error: errorMessage
      })
    }
  

  logger.info('日単位データ取得完了', { date, totalDataTypes: dataTypes.length, successCount: results.filter(r => r.success).length })

  return results
}

