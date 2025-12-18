import { logger } from 'firebase-functions'
import { getAuth } from 'firebase-admin/auth'
import { getFirestore } from 'firebase-admin/firestore'
import * as fs from 'fs'
import * as path from 'path'
import { cleanupTempFile, createTempDir, uploadFileToStorage } from '../utils/storageUploader'

type UploadModelRequestBody = {
  fileName: string
  contentBase64: string
  modelName: string
  storagePath: string
  version?: string
  description?: string
  trainingDate?: string
}

function requireString(value: unknown, fieldName: string): string {
  if (typeof value !== 'string' || value.trim().length === 0) throw new Error(`${fieldName} is required`)
  return value.trim()
}

function parseBearerToken(authHeader: unknown): string {
  const header = typeof authHeader === 'string' ? authHeader : ''
  const [scheme, token] = header.split(' ')
  if (scheme !== 'Bearer' || !token) throw new Error('Authorization: Bearer <token> is required')
  return token
}

function isDevelopmentEnv(): boolean {
  return process.env.NODE_ENV === 'development' || process.env.FUNCTIONS_EMULATOR === 'true' || process.env.MODE === 'development'
}

export async function handleUploadModel(request: any, response: any): Promise<void> {
  const startTime = Date.now()
  try {
    if (request.method !== 'POST') {
      response.status(405).send({ success: false, error: 'Method not allowed' })
      return
    }

    const token = parseBearerToken(request.headers?.authorization)
    const decoded = await getAuth().verifyIdToken(token)

    // 本番では管理者のみ許可。エミュレータでは、管理者クレーム未整備のため「認証済み」までで許可する。
    if (!isDevelopmentEnv()) {
      const role = (decoded as any)?.role
      if (role !== 'admin') throw new Error('Admin role is required')
    }

    const body = request.body as Partial<UploadModelRequestBody>
    const fileName = requireString(body.fileName, 'fileName')
    const contentBase64 = requireString(body.contentBase64, 'contentBase64')
    const modelName = requireString(body.modelName, 'modelName')
    const storagePath = requireString(body.storagePath, 'storagePath')

    if (!storagePath.startsWith('models/')) throw new Error(`storagePath must start with "models/": ${storagePath}`)
    if (!/^[a-zA-Z0-9._/-]+$/.test(storagePath)) throw new Error(`storagePath contains invalid characters: ${storagePath}`)

    const buffer = Buffer.from(contentBase64, 'base64')
    if (buffer.length === 0) throw new Error('contentBase64 decoded to empty buffer')

    const tempDir = createTempDir()
    const tempFilePath = path.join(tempDir, fileName)
    fs.writeFileSync(tempFilePath, buffer)

    try {
      await uploadFileToStorage(tempFilePath, storagePath, {
        model_name: modelName,
        uploaded_by_uid: decoded.uid,
        original_file_name: fileName
      })
    } finally {
      cleanupTempFile(tempFilePath)
    }

    const storageEmulatorHost = process.env.STORAGE_EMULATOR_HOST
    const storageUrl = storageEmulatorHost
      ? `http://${storageEmulatorHost}/umayomi-fbb2b.firebasestorage.app/${storagePath}`
      : `gs://umayomi-fbb2b.firebasestorage.app/${storagePath}`

    const now = new Date()
    const db = getFirestore()
    await db.collection('models').doc(modelName).set({
      model_name: modelName,
      storage_path: storagePath,
      storage_url: storageUrl,
      is_active: true, // デフォルトで有効
      ...(body.version ? { version: body.version } : {}),
      ...(body.description ? { description: body.description } : {}),
      ...(body.trainingDate ? { training_date: body.trainingDate } : {}),
      created_at: now,
      updated_at: now
    }, { merge: true })

    response.status(200).send({
      success: true,
      modelName,
      storagePath,
      storageUrl,
      executionTimeMs: Date.now() - startTime
    })
  } catch (e: any) {
    const errorMessage = e instanceof Error ? e.message : String(e)
    logger.error('uploadModel failed', { error: errorMessage })
    response.status(400).send({
      success: false,
      error: errorMessage
    })
  }
}


