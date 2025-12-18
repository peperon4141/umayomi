import { logger } from 'firebase-functions'
import { exec } from 'child_process'
import { promisify } from 'util'
import * as path from 'path'
import * as fs from 'fs'
import { getFirestore } from 'firebase-admin/firestore'

const execAsync = promisify(exec)

function validateJrdbRaceId(raceId: string): void {
  const parts = raceId.split('_')
  if (parts.length !== 4) throw new Error(`Invalid race_key format (expected 場コード_回_日目_R): ${raceId}`)
  const [placeCode, kaisaiRound, kaisaiDay, raceNumber] = parts
  if (!/^\d{2}$/.test(placeCode)) throw new Error(`Invalid placeCode in race_key: ${raceId}`)
  if (!/^\d+$/.test(kaisaiRound)) throw new Error(`Invalid kaisaiRound in race_key: ${raceId}`)
  if (!/^[0-9a-z]+$/.test(kaisaiDay)) throw new Error(`Invalid kaisaiDay in race_key: ${raceId}`)
  if (!/^\d{2}$/.test(raceNumber)) throw new Error(`Invalid raceNumber in race_key: ${raceId}`)
}

async function linkPredictionsToRacesByDate(targetDate: string): Promise<{ updated: number; racesMatched: number; uniquePredictionRaces: number }> {
  const db = getFirestore()
  const docId = `date_${targetDate.replace(/-/g, '_')}`
  const predRef = db.collection('predictions').doc(docId)
  const predSnap = await predRef.get()
  if (!predSnap.exists) throw new Error(`predictions doc not found: predictions/${docId}`)

  const predData = predSnap.data() as any
  const predictions = predData?.predictions
  if (!Array.isArray(predictions)) throw new Error(`predictions field is missing or not an array: predictions/${docId}`)

  const uniqueRaceKeys = Array.from(new Set(predictions.map((p: any) => p?.race_key).filter((rk: any) => typeof rk === 'string')))
  uniqueRaceKeys.forEach(validateJrdbRaceId)
  const uniquePredictionRaces = uniqueRaceKeys.length
  const uniqueRaceKeySet = new Set(uniqueRaceKeys)

  const start = new Date(`${targetDate}T00:00:00.000Z`)
  const end = new Date(`${targetDate}T00:00:00.000Z`)
  end.setUTCDate(end.getUTCDate() + 1)
  const year = parseInt(targetDate.slice(0, 4), 10)

  const racesSnap = await db.collection('racesByYear').doc(String(year)).collection('races')
    .where('raceDate', '>=', start)
    .where('raceDate', '<', end)
    .get()

  if (racesSnap.empty) throw new Error(`No races found for date: ${targetDate}`)

  let updated = 0
  let racesMatched = 0
  const batch = db.batch()

  racesSnap.docs.forEach((doc) => {
    if (!uniqueRaceKeySet.has(doc.id)) return
    racesMatched += 1
    batch.update(doc.ref, {
      prediction_linked_at: new Date(),
      prediction_date: targetDate,
      updatedAt: new Date()
    })
    updated += 1
  })

  await batch.commit()
  return { updated, racesMatched, uniquePredictionRaces }
}

/**
 * 最新の有効なモデルをFirestoreから取得
 */
async function getLatestModelFromFirestore(): Promise<string | null> {
  try {
    const db = getFirestore()
    const modelsCollection = db.collection('models')
    
    // 有効なモデルのみを取得（is_active=true または is_activeが未設定）
    // 作成日時の降順でソートして最新のモデルを取得
    // 注意: Firestoreでは複数のwhere条件でORが使えないため、まず全て取得してフィルタリング
    const snapshot = await modelsCollection
      .orderBy('created_at', 'desc')
      .limit(50) // 最新50件を取得してフィルタリング
      .get()
    
    if (snapshot.empty) {
      logger.warn('No models found in Firestore')
      return null
    }
    
    // is_activeがtrueまたは未設定（undefined/null）のモデルをフィルタリング
    const activeModels = snapshot.docs.filter((doc) => {
      const data = doc.data()
      const isActive = data.is_active
      // is_activeがtrue、または未設定（undefined/null）の場合は有効とみなす
      return isActive === true || isActive === undefined || isActive === null
    })
    
    if (activeModels.length === 0) {
      logger.warn('No active models found in Firestore')
      return null
    }
    
    const modelDoc = activeModels[0] // 既にcreated_atでソート済み
    const modelData = modelDoc.data()
    const storagePath = modelData.storage_path as string
    
    logger.info('Latest active model found', {
      modelName: modelDoc.id,
      storagePath,
      isActive: modelData.is_active
    })
    
    return storagePath
  } catch (error: any) {
    logger.error('Failed to get latest active model from Firestore', { error: error.message })
    return null
  }
}

/**
 * Pythonスクリプトを実行してdailyデータを取得・分析・Firestoreに保存する
 */
export async function handleRunDailyPrediction(request: any, response: any): Promise<void> {
  const startTime = Date.now()
  logger.info('Daily prediction function called')

  try {
    // パラメータの取得
    const date = request.query.date || request.body.date
    let modelStoragePath = request.query.modelStoragePath || request.body.modelStoragePath
    const useEmulator = request.query.useEmulator === 'true' || request.body.useEmulator === true
    const autoSelectModel = request.query.autoSelectModel === 'true' || request.body.autoSelectModel === true

    // モデルパスが指定されていない場合、最新のモデルを自動選択
    if (!modelStoragePath && autoSelectModel) {
      logger.info('Auto-selecting latest model from Firestore')
      modelStoragePath = await getLatestModelFromFirestore()
      
      if (!modelStoragePath) {
        const errorMessage = 'No model found in Firestore. Please upload a model first or specify modelStoragePath.'
        logger.error(errorMessage)
        response.status(400).send({
          success: false,
          error: errorMessage
        })
        return
      }
      
      logger.info('Latest model selected', { modelStoragePath })
    }

    if (!modelStoragePath) {
      const errorMessage = 'modelStoragePath parameter is required (or set autoSelectModel=true)'
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
      useEmulator,
      autoSelectModel
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

    // Pythonコマンドを決定（仮想環境のPythonを使用）
    const predictionDir = path.join(process.cwd(), '..', '..', 'apps', 'prediction')
    const venvPython = path.join(predictionDir, '.venv', 'bin', 'python')
    const pythonCmd = fs.existsSync(venvPython) ? venvPython : (process.env.PYTHON_COMMAND || 'python3')
    const emulatorFlag = useEmulator ? '--use-emulator' : ''
    const command = `${pythonCmd} "${scriptPath}" --date "${targetDate}" --model-storage-path "${modelStoragePath}" ${emulatorFlag}`

    logger.info('Executing Python script', { command, pythonCmd })

    // Pythonスクリプトを実行
    const { stdout, stderr } = await execAsync(command, {
      cwd: path.dirname(scriptPath),
      env: {
        ...process.env,
        PYTHONPATH: path.join(process.cwd(), '..', '..', 'apps', 'prediction'),
        USE_FIREBASE_EMULATOR: useEmulator ? 'true' : 'false',
        PATH: `${path.join(predictionDir, '.venv', 'bin')}:${process.env.PATH}` // 仮想環境のbinをPATHに追加
      },
      maxBuffer: 10 * 1024 * 1024 // 10MB
    })

    if (stderr) logger.warn('Python script stderr', { stderr })

    logger.info('Python script completed', { stdout })

    const executionTimeMs = Date.now() - startTime
    const message = `Daily prediction completed for ${targetDate}`

    response.status(200).send({
      success: true,
      message,
      date: targetDate,
      modelStoragePath,
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

/**
 * JRDBデータ取得と予測実行を統合したCloud Function
 * predict_and_save_to_firestore.pyを再利用（既にデータ取得・結合・予測・Firestore保存を含む）
 */
export async function handleRunPredictionWithDataFetch(request: any, response: any): Promise<void> {
  const startTime = Date.now()
  logger.info('Prediction with data fetch function called')

  const tail = (text: string, maxChars: number) => (text.length <= maxChars ? text : text.slice(-maxChars))

  const getProjectIdFromEnv = (): string => {
    const direct = process.env.GCLOUD_PROJECT
    if (direct && direct.length > 0) return direct
    const gcp = process.env.GCP_PROJECT
    if (gcp && gcp.length > 0) return gcp
    const firebaseConfig = process.env.FIREBASE_CONFIG
    if (!firebaseConfig) throw new Error('GCLOUD_PROJECT (or FIREBASE_CONFIG) is required (no fallback).')
    let parsed: any
    try {
      parsed = JSON.parse(firebaseConfig)
    } catch {
      throw new Error('FIREBASE_CONFIG must be a valid JSON string.')
    }
    const projectId = parsed?.projectId
    if (typeof projectId !== 'string' || projectId.length === 0) throw new Error('FIREBASE_CONFIG.projectId is required (no fallback).')
    return projectId
  }

  try {
    // パラメータの取得
    const date = request.query.date || request.body.date
    const useEmulator = request.query.useEmulator === 'true' || request.body.useEmulator === true
    const autoSelectModel = request.query.autoSelectModel !== 'false' // デフォルトでtrue

    // 日付の決定（省略時は今日）
    const targetDate = date || new Date().toISOString().split('T')[0]

    logger.info('Starting prediction with data fetch', {
      date: targetDate,
      useEmulator,
      autoSelectModel
    })

    // 1. 最新のモデルを取得
    let modelStoragePath: string | null = null
    if (autoSelectModel) {
      modelStoragePath = await getLatestModelFromFirestore()
      if (!modelStoragePath) {
        const errorMessage = 'No model found in Firestore. Please upload a model first.'
        logger.error(errorMessage)
        response.status(400).send({
          success: false,
          error: errorMessage
        })
        return
      }
      logger.info('Latest model selected', { modelStoragePath })
    } else {
      modelStoragePath = request.query.modelStoragePath || request.body.modelStoragePath
      if (!modelStoragePath) {
        const errorMessage = 'modelStoragePath parameter is required (or set autoSelectModel=true)'
        logger.error(errorMessage)
        response.status(400).send({
          success: false,
          error: errorMessage
        })
        return
      }
    }

    // 2. 予測実行スクリプトのパス（既にデータ取得・結合・予測・Firestore保存を含む）
    const predictScriptPath = path.join(
      process.cwd(),
      '..',
      '..',
      'apps',
      'prediction',
      'scripts',
      'predict_and_save_to_firestore.py'
    )

    // スクリプトが存在するか確認
    if (!fs.existsSync(predictScriptPath)) {
      const errorMessage = `Predict script not found: ${predictScriptPath}`
      logger.error(errorMessage)
      response.status(500).send({
        success: false,
        error: errorMessage
      })
      return
    }

    // Pythonコマンドを決定（仮想環境のPythonを使用）
    const predictionDir = path.join(process.cwd(), '..', '..', 'apps', 'prediction')
    const venvPython = path.join(predictionDir, '.venv', 'bin', 'python')
    const pythonCmd = fs.existsSync(venvPython) ? venvPython : (process.env.PYTHON_COMMAND || 'python3')
    const emulatorFlag = useEmulator ? '--use-emulator' : ''
    const projectId = useEmulator ? getProjectIdFromEnv() : null

    // 3. 予測実行（predict_and_save_to_firestore.pyがデータ取得・結合・予測・Firestore保存を実行）
    logger.info('Running prediction with data fetch', { modelStoragePath, date: targetDate, pythonCmd })
    const command = `${pythonCmd} "${predictScriptPath}" --date "${targetDate}" --model-storage-path "${modelStoragePath}" ${emulatorFlag}`

    logger.info('Executing Python script', { command })

    let stdout = ''
    let stderr = ''
    try {
      const result = await execAsync(command, {
        cwd: path.dirname(predictScriptPath),
        env: {
          ...process.env,
          PYTHONPATH: path.join(process.cwd(), '..', '..', 'apps', 'prediction'),
          USE_FIREBASE_EMULATOR: useEmulator ? 'true' : 'false',
          ...(useEmulator ? { GCLOUD_PROJECT: projectId as string } : {}),
          PATH: `${path.join(predictionDir, '.venv', 'bin')}:${process.env.PATH}` // 仮想環境のbinをPATHに追加
        },
        maxBuffer: 10 * 1024 * 1024 // 10MB
      })
      stdout = result.stdout || ''
      stderr = result.stderr || ''
    } catch (e: any) {
      stdout = typeof e?.stdout === 'string' ? e.stdout : ''
      stderr = typeof e?.stderr === 'string' ? e.stderr : ''
      const errMessage = e instanceof Error ? e.message : String(e)
      logger.error('Python script failed', { errMessage, stderrTail: tail(stderr, 4000), stdoutTail: tail(stdout, 2000) })
      response.status(500).send({
        success: false,
        error: 'Python script failed',
        errorDetails: errMessage,
        stderr: tail(stderr, 4000),
        stdout: tail(stdout, 2000)
      })
      return
    }

    if (stderr) logger.warn('Python script stderr', { stderr })
    logger.info('Python script completed', { stdout })

    let linking: { updated: number; racesMatched: number; uniquePredictionRaces: number } | null = null
    let linkingError: string | null = null
    try {
      linking = await linkPredictionsToRacesByDate(targetDate)
      logger.info('Linked predictions to races', linking)
    } catch (e: any) {
      linkingError = e instanceof Error ? e.message : String(e)
      logger.error('Failed to link predictions to races', { error: linkingError })
    }

    const executionTimeMs = Date.now() - startTime
    const message = `Prediction with data fetch completed for ${targetDate}`

    response.status(200).send({
      success: true,
      message,
      date: targetDate,
      modelStoragePath,
      executionTimeMs,
      linking,
      linkingError,
      stdout: stdout.substring(0, 2000) // 最初の2000文字のみ返す
    })

  } catch (error: any) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('Prediction with data fetch failed', {
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
