import { logger } from 'firebase-functions'
import { downloadJRDBFile } from './downloader'
import { convertLzhToParquet } from './converter'
import { generateJRDBRaceKey, generateJRDBDataFileUrl, getKYDataTypes } from './raceKeyGenerator'
import { getJRDBFileUrlFromMemberPage } from './memberPageParser'
import { getFirestore } from 'firebase-admin/firestore'
import { JRDBDataType } from '../../../shared/src/jrdb'
import * as path from 'path'
import * as fs from 'fs'
import { createTempDir, uploadJRDBParquetToStorageWithFileName } from '../utils/storageUploader'

/**
 * KY系データ（KYI/KYH/KYG/KKA）を取得してFirestoreに保存
 * @param year - 年
 * @param month - 月
 * @param day - 日
 * @param racecourse - 競馬場名
 * @param kaisaiRound - 開催回数
 * @param kaisaiDay - 日目
 * @param raceNumber - レース番号
 */
export async function fetchRaceKYData(
  year: number,
  month: number,
  day: number,
  racecourse: string,
  kaisaiRound: number,
  kaisaiDay: number,
  raceNumber: number
): Promise<{
  raceKey: string
  dataTypes: string[]
  results: Array<{
    dataType: string
    success: boolean
    storagePath?: string
    fileName?: string
    error?: string
  }>
}> {
  const raceKey = generateJRDBRaceKey(year, month, day, racecourse, kaisaiRound, kaisaiDay, raceNumber)
  // JRDBのファイル名形式: YYMMDD（年を2桁で表現）
  const year2Digit = String(year).slice(-2)
  const dateStr = `${year2Digit}${String(month).padStart(2, '0')}${String(day).padStart(2, '0')}`
  
  logger.info('KY系データ取得開始', { raceKey })

  const kyDataTypes = getKYDataTypes()
  const results: Array<{
    dataType: JRDBDataType
    success: boolean
    storagePath?: string
    fileName?: string
    error?: string
  }> = []

  const db = getFirestore()
  const tempDir = createTempDir()

  try {
    for (const dataType of kyDataTypes) {
      try {
        // 1. JRDBメンバーページから実際のファイルURLを取得
        let dataFileUrl: string | null = null
        try {
          dataFileUrl = await getJRDBFileUrlFromMemberPage(dataType, dateStr)
        } catch {
          // フォールバックURLを使用（エラーログは出力しない）
        }
        
        // メンバーページから取得できなかった場合は、直接URLを生成（フォールバック）
        if (!dataFileUrl) {
          dataFileUrl = generateJRDBDataFileUrl(dataType, dateStr)
        }

        // 2. ファイルをダウンロード
        const lzhBuffer = await downloadJRDBFile(dataFileUrl)

        // 3. Parquetに変換（パースしたデータも取得）
        const parquetPath = path.join(tempDir, `${dataType}_${dateStr}.parquet`)
        const { records } = await convertLzhToParquet(
          lzhBuffer,
          dataType,
          year,
          parquetPath
        )
        
        // 3-1. 特定のレースキーにマッチするレコードをフィルタリング
        // KYIデータのレースキーは「年月日8桁+場コード2桁+開催回数1桁+日目1桁+レース番号2桁+馬番2桁」の形式
        // fetchRaceKYDataのraceKeyは「年月日8桁+場コード2桁+開催回数1桁+日目1桁+レース番号2桁」の形式
        // したがって、レコードのレースキーの先頭12桁（馬番を除く）で比較する
        const raceRecords = records.filter((record) => {
          const recordRaceKey = record['レースキー'] as string
          if (!recordRaceKey) {
            return false
          }
          // レースキーの先頭12桁（馬番を除く）で比較
          return recordRaceKey.startsWith(raceKey)
        })
        
        if (raceRecords.length === 0 && records.length > 0) {
          logger.warn('レースキーにマッチするレコードが見つかりませんでした', {
            dataType,
            raceKey,
            totalRecords: records.length
          })
        }

        // 4. ParquetファイルをStorageにアップロード
        const fileName = `${dataType}${dateStr}`
        if (!fs.existsSync(parquetPath)) {
          throw new Error(`Parquetファイルが存在しません: ${parquetPath}`)
        }
        
        const storagePath = await uploadJRDBParquetToStorageWithFileName(parquetPath, fileName)
        
        if (!storagePath) {
          throw new Error('Storageへのアップロードに失敗しました: storagePathが返されませんでした')
        }

        // 5. Firestoreにメタデータとパースしたデータを保存
        const docRef = db.collection('jrdb_race_data').doc(raceKey)
        const kyDataRef = docRef.collection('ky_data').doc(dataType)
        
        await kyDataRef.set({
          dataType,
          raceKey,
          date: new Date(year, month - 1, day),
          racecourse,
          raceNumber,
          kaisaiRound,
          kaisaiDay,
          storagePath,
          fileName,
          records: raceRecords,
          recordCount: raceRecords.length,
          fetchedAt: new Date()
        }, { merge: true })

        results.push({
          dataType,
          success: true,
          storagePath,
          fileName
        })

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error)
        logger.error(`KY系データ取得エラー: ${dataType}`, {
          dataType,
          raceKey,
          error: errorMessage
        })

        results.push({
          dataType,
          success: false,
          error: errorMessage
        })
      }
    }

    // レースキー情報をFirestoreに保存
    const raceDocRef = db.collection('jrdb_race_data').doc(raceKey)
    await raceDocRef.set({
      raceKey,
      date: new Date(year, month - 1, day),
      racecourse,
      raceNumber,
      kaisaiRound,
      kaisaiDay,
      kyDataFetched: true,
      kyDataTypes: results.filter(r => r.success).map(r => r.dataType),
      updatedAt: new Date()
    }, { merge: true })

    logger.info('KY系データ取得完了', { raceKey })

    return {
      raceKey,
      dataTypes: kyDataTypes,
      results
    }

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    logger.error('KY系データ取得処理全体でエラー', {
      raceKey,
      error: errorMessage
    })
    throw error
  } finally {
    // 一時ファイルをクリーンアップ
    try {
      if (fs.existsSync(tempDir)) {
        fs.rmSync(tempDir, { recursive: true, force: true })
      }
    } catch {
      // クリーンアップエラーは無視
    }
  }
}

