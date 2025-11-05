import { logger } from 'firebase-functions'
import { downloadJRDBFile } from './downloader'
import { extractLzhFile } from './converter'
import { generateJRDBDataFileUrl } from './raceKeyGenerator'
import { getJRDBFileUrlFromMemberPage } from './memberPageParser'
import { parseJRDBDataFromBuffer } from './parsers/jrdbParser'
import { JRDBDataType } from '../../../shared/src/jrdb'
import { getFirestore } from 'firebase-admin/firestore'
import { createTempDir, uploadJRDBParquetToStorageWithFileName } from '../utils/storageUploader'
import * as path from 'path'
import * as fs from 'fs'
import { convertLzhToParquet } from './converter'

/**
 * 日単位でKYIデータを取得してFirestoreに保存
 * @param year - 年
 * @param month - 月
 * @param day - 日
 */
export async function fetchDailyKYIData(
  year: number,
  month: number,
  day: number
): Promise<{
  date: string
  success: boolean
  recordCount: number
  storagePath?: string
  fileName?: string
  error?: string
}> {
  const year2Digit = String(year).slice(-2)
  const dateStr = `${year2Digit}${String(month).padStart(2, '0')}${String(day).padStart(2, '0')}`
  const date = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  const dataType = JRDBDataType.KYI

  logger.info('KYIデータ取得開始', { date })

  const db = getFirestore()
  const tempDir = createTempDir()

  try {
    // 1. ファイルURL取得
    let dataFileUrl: string | null = null
    try {
      dataFileUrl = await getJRDBFileUrlFromMemberPage(dataType, dateStr)
    } catch {
      // フォールバックURLを使用
    }
    if (!dataFileUrl) dataFileUrl = generateJRDBDataFileUrl(dataType, dateStr)

    // 2. ダウンロード・展開・パース
    const lzhBuffer = await downloadJRDBFile(dataFileUrl)
    const extractedBuffer = await extractLzhFile(lzhBuffer)
    const records = parseJRDBDataFromBuffer(extractedBuffer, dataType)

    if (records.length === 0) throw new Error('パースされたレコードが0件です')

    // 3. レースキーごとにグループ化
    const recordsByRaceKey = new Map<string, Record<string, unknown>[]>()
    for (const record of records) {
      const raceKey = record['レースキー'] as string
      if (!raceKey) continue
      if (!recordsByRaceKey.has(raceKey)) recordsByRaceKey.set(raceKey, [])
      recordsByRaceKey.get(raceKey)!.push(record)
    }

    // 4. Firestoreに保存（レースキーごと）
    const batch = db.batch()
    let batchCount = 0
    const maxBatchSize = 500

    for (const [raceKey, raceRecords] of recordsByRaceKey.entries()) {
      const docRef = db.collection('jrdb_daily_data').doc(date).collection('kyi_data').doc(raceKey)
      batch.set(docRef, {
        date,
        raceKey,
        records: raceRecords,
        recordCount: raceRecords.length,
        fetchedAt: new Date()
      }, { merge: true })

      batchCount++
      if (batchCount >= maxBatchSize) {
        await batch.commit()
        batchCount = 0
      }
    }
    if (batchCount > 0) await batch.commit()

    // 5. Parquetファイルを生成してStorageに保存
    const parquetPath = path.join(tempDir, `${dataType}_${dateStr}.parquet`)
    await convertLzhToParquet(lzhBuffer, dataType, year, parquetPath)
    const fileName = `${dataType}${dateStr}`
    const storagePath = await uploadJRDBParquetToStorageWithFileName(parquetPath, fileName)

    // 6. 日単位のメタデータを保存
    await db.collection('jrdb_daily_data').doc(date).set({
      date,
      year,
      month,
      day,
      dataType,
      recordCount: records.length,
      raceKeyCount: recordsByRaceKey.size,
      storagePath,
      fileName,
      fetchedAt: new Date()
    }, { merge: true })

    return {
      date,
      success: true,
      recordCount: records.length,
      storagePath,
      fileName
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    logger.error('KYIデータ取得エラー', { date, error: errorMessage })

    return {
      date,
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

