import { logger } from 'firebase-functions'
import { exec } from 'child_process'
import { promisify } from 'util'
import * as path from 'path'
import * as fs from 'fs'
import { getFirestore, Timestamp } from 'firebase-admin/firestore'

const execAsync = promisify(exec)

/**
 * Pythonスクリプトを実行してdailyデータを取得する（データ取得のみ）
 */
export async function handleFetchJRDBDailyDataOnly(request: any, response: any): Promise<void> {
  const startTime = Date.now()
  logger.info('Fetch JRDB daily data only function called')

  try {
    // パラメータの取得
    const date = request.query.date || request.body.date
    const year = request.query.year || request.body.year
    const month = request.query.month || request.body.month
    const day = request.query.day || request.body.day

    // 日付の決定
    let targetDate: string
    let yearParam: number | undefined
    let monthParam: number | undefined
    let dayParam: number | undefined

    if (date) {
      targetDate = date
    } else if (year && month && day) {
      yearParam = parseInt(String(year))
      monthParam = parseInt(String(month))
      dayParam = parseInt(String(day))
      targetDate = `${yearParam}-${String(monthParam).padStart(2, '0')}-${String(dayParam).padStart(2, '0')}`
    } else {
      const errorMessage = 'date parameter or (year, month, day) parameters are required'
      logger.error(errorMessage)
      response.status(400).send({
        success: false,
        error: errorMessage
      })
      return
    }

    logger.info('Starting JRDB daily data fetch', {
      date: targetDate,
      year: yearParam,
      month: monthParam,
      day: dayParam
    })

    // Pythonスクリプトのパス
    const scriptPath = path.join(
      process.cwd(),
      '..',
      '..',
      'apps',
      'prediction',
      'scripts',
      'fetch_daily_data_only.py'
    )

    // スクリプトが存在するか確認
    if (!fs.existsSync(scriptPath)) {
      const errorMessage = `Python script not found: ${scriptPath}`
      logger.error(errorMessage)
      response.status(500).send({
        success: false,
        error: errorMessage
      })
      return
    }

    // Pythonコマンドを構築
    const pythonCmd = process.env.PYTHON_COMMAND || 'python3'
    let command: string
    
    if (targetDate) {
      command = `${pythonCmd} "${scriptPath}" --date "${targetDate}"`
    } else {
      command = `${pythonCmd} "${scriptPath}" --year ${yearParam} --month ${monthParam} --day ${dayParam}`
    }

    logger.info('Executing Python script', { command })

    // Pythonスクリプトを実行
    const { stdout, stderr } = await execAsync(command, {
      cwd: path.dirname(scriptPath),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), '..', '..', 'apps', 'prediction')
      },
      maxBuffer: 10 * 1024 * 1024 // 10MB
    })

    if (stderr) logger.warn('Python script stderr', { stderr })

    logger.info('Python script completed', { stdout })

    // データ取得が成功した場合、ParquetデータをJSON形式でエクスポートしてFirestoreに保存
    let savedToFirestore = false
    let firestoreResult: any = null
    
    try {
      // 日次データフォルダのパス
      const dailyFolder = path.join(
        process.cwd(),
        '..',
        '..',
        'data',
        'daily',
        String(monthParam || new Date(targetDate).getMonth() + 1).padStart(2, '0'),
        String(dayParam || new Date(targetDate).getDate()).padStart(2, '0')
      )

      if (fs.existsSync(dailyFolder)) {
        // ParquetデータをJSON形式でエクスポートするPythonスクリプトを実行
        const exportScriptPath = path.join(
          process.cwd(),
          '..',
          '..',
          'apps',
          'prediction',
          'scripts',
          'export_daily_data_to_json.py'
        )

        if (fs.existsSync(exportScriptPath)) {
          const pythonCmd = process.env.PYTHON_COMMAND || 'python3'
          const exportCommand = `${pythonCmd} "${exportScriptPath}" --date "${targetDate}" --daily-folder "${dailyFolder}"`
          
          logger.info('Exporting Parquet data to JSON', { command: exportCommand })
          
          const { stdout: exportStdout, stderr: exportStderr } = await execAsync(exportCommand, {
            cwd: path.dirname(exportScriptPath),
            env: {
              ...process.env,
              PYTHONPATH: path.join(process.cwd(), '..', '..', 'apps', 'prediction')
            },
            maxBuffer: 50 * 1024 * 1024 // 50MB（JSONデータが大きい可能性があるため）
          })

          if (exportStderr) logger.warn('Export script stderr', { stderr: exportStderr })

          // JSON出力を抽出
          const jsonMatch = exportStdout.match(/=== エクスポート結果 ===\s*([\s\S]*)/)
          if (jsonMatch) {
            const exportResult = JSON.parse(jsonMatch[1])
            
            // Firestoreに保存
            firestoreResult = await saveJRDBDataToFirestore(exportResult, targetDate)
            savedToFirestore = true
            
            logger.info('JRDB data saved to Firestore', {
              date: targetDate,
              dataTypes: Object.keys(exportResult.dataTypes || {}),
              firestoreResult
            })
          }
        } else {
          logger.warn('Export script not found', { exportScriptPath })
        }
      } else {
        logger.warn('Daily folder not found', { dailyFolder })
      }
    } catch (error: any) {
      logger.error('Failed to save JRDB data to Firestore', {
        error: error instanceof Error ? error.message : String(error),
        stack: error instanceof Error ? error.stack : undefined
      })
      // Firestore保存の失敗は処理を停止させない
    }

    const executionTimeMs = Date.now() - startTime
    const message = `JRDB daily data fetch completed for ${targetDate}`

    // stdoutから結果サマリーを抽出（JSON形式で出力されている場合）
    let resultSummary: any = null
    try {
      const summaryMatch = stdout.match(/=== 結果サマリー ===\s*([\s\S]*)/)
      if (summaryMatch) {
        resultSummary = JSON.parse(summaryMatch[1])
      }
    } catch (e) {
      logger.warn('Failed to parse result summary from stdout', { error: e })
    }

    response.status(200).send({
      success: true,
      message,
      date: targetDate,
      executionTimeMs,
      resultSummary,
      savedToFirestore,
      firestoreResult,
      stdout: stdout.substring(0, 2000) // 最初の2000文字のみ返す
    })

  } catch (error: any) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('JRDB daily data fetch failed', {
      error: errorMessage,
      stack: errorStack
    })

    response.status(500).send({
      success: false,
      error: errorMessage,
      details: errorStack
    })
  }
}

/**
 * JRDBデータをFirestoreのサブコレクションに保存
 * 構造: races/{race_key}/jrdb_data/{dataType}
 */
async function saveJRDBDataToFirestore(
  exportResult: any,
  date: string
): Promise<{ savedRaceKeys: number, savedRecords: number, errors: string[] }> {
  const db = getFirestore()
  const savedRaceKeys = new Set<string>()
  let savedRecords = 0
  const errors: string[] = []

  try {
    const dataTypes = exportResult.dataTypes || {}
    
    for (const [dataType, dataTypeResult] of Object.entries(dataTypes)) {
      const typedResult = dataTypeResult as any
      
      if (!typedResult.success || !typedResult.groupedByRaceKey) {
        logger.warn(`Skipping ${dataType} due to failure or missing data`, {
          success: typedResult.success,
          hasGroupedData: !!typedResult.groupedByRaceKey
        })
        continue
      }

      const groupedByRaceKey = typedResult.groupedByRaceKey as Record<string, any[]>
      
      // 各race_keyごとにバッチで保存
      for (const [raceKey, records] of Object.entries(groupedByRaceKey)) {
        if (!raceKey || records.length === 0) {
          continue
        }

        try {
          // races/{race_key}/jrdb_data/{dataType} に保存
          const raceRef = db.collection('races').doc(raceKey)
          const jrdbDataRef = raceRef.collection('jrdb_data').doc(dataType)
          
          // メタデータとレコードを保存
          await jrdbDataRef.set({
            dataType,
            date,
            recordCount: records.length,
            fetchedAt: Timestamp.now(),
            updatedAt: Timestamp.now()
          }, { merge: true })

          // レコードをサブコレクションに保存
          const recordsRef = jrdbDataRef.collection('records')
          let batch = db.batch()
          let batchCount = 0
          const maxBatchSize = 500

          for (let i = 0; i < records.length; i++) {
            const record = records[i]
            const recordRef = recordsRef.doc(String(i))
            batch.set(recordRef, {
              ...record,
              index: i
            })
            batchCount++
            savedRecords++

            if (batchCount >= maxBatchSize) {
              await batch.commit()
              batch = db.batch()
              batchCount = 0
            }
          }

          if (batchCount > 0) {
            await batch.commit()
          }

          savedRaceKeys.add(raceKey)
          
          logger.info(`Saved ${dataType} data for race_key: ${raceKey}`, {
            raceKey,
            dataType,
            recordCount: records.length
          })
        } catch (error: any) {
          const errorMessage = `Failed to save ${dataType} for race_key ${raceKey}: ${error instanceof Error ? error.message : String(error)}`
          errors.push(errorMessage)
          logger.error(errorMessage, {
            raceKey,
            dataType,
            error: error instanceof Error ? error.stack : undefined
          })
        }
      }
    }

    return {
      savedRaceKeys: savedRaceKeys.size,
      savedRecords,
      errors
    }
  } catch (error: any) {
    const errorMessage = `Failed to save JRDB data to Firestore: ${error instanceof Error ? error.message : String(error)}`
    errors.push(errorMessage)
    logger.error(errorMessage, {
      error: error instanceof Error ? error.stack : undefined
    })
    return {
      savedRaceKeys: savedRaceKeys.size,
      savedRecords,
      errors
    }
  }
}

