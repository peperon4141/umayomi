import { logger } from 'firebase-functions'
import { exec } from 'child_process'
import { promisify } from 'util'
import * as path from 'path'
import * as fs from 'fs'

const execAsync = promisify(exec)

/**
 * Pythonスクリプトを実行してdailyデータを取得・分析・Firestoreに保存する
 */
export async function handleRunDailyPrediction(request: any, response: any): Promise<void> {
  const startTime = Date.now()
  logger.info('Daily prediction function called')

  try {
    // パラメータの取得
    const date = request.query.date || request.body.date
    const modelStoragePath = request.query.modelStoragePath || request.body.modelStoragePath
    const useEmulator = request.query.useEmulator === 'true' || request.body.useEmulator === true

    if (!modelStoragePath) {
      const errorMessage = 'modelStoragePath parameter is required'
      logger.error(errorMessage)
      response.status(400).send({
        success: false,
        error: errorMessage
      })
      return
    }

    // 日付の決定（省略時は今日）
    const targetDate = date || new Date().toISOString().split('T')[0]

    logger.info('Starting daily prediction', {
      date: targetDate,
      modelStoragePath,
      useEmulator
    })

    // Pythonスクリプトのパス
    const scriptPath = path.join(
      process.cwd(),
      '..',
      '..',
      'apps',
      'prediction',
      'scripts',
      'predict_and_save_to_firestore.py'
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
    const emulatorFlag = useEmulator ? '--use-emulator' : ''
    const command = `${pythonCmd} "${scriptPath}" --date "${targetDate}" --model-storage-path "${modelStoragePath}" ${emulatorFlag}`

    logger.info('Executing Python script', { command })

    // Pythonスクリプトを実行
    const { stdout, stderr } = await execAsync(command, {
      cwd: path.dirname(scriptPath),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), '..', '..', 'apps', 'prediction'),
        USE_FIREBASE_EMULATOR: useEmulator ? 'true' : 'false'
      },
      maxBuffer: 10 * 1024 * 1024 // 10MB
    })

    if (stderr) {
      logger.warn('Python script stderr', { stderr })
    }

    logger.info('Python script completed', { stdout })

    const executionTimeMs = Date.now() - startTime
    const message = `Daily prediction completed for ${targetDate}`

    response.status(200).send({
      success: true,
      message,
      date: targetDate,
      executionTimeMs,
      stdout: stdout.substring(0, 1000) // 最初の1000文字のみ返す
    })

  } catch (error: any) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('Daily prediction failed', {
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

