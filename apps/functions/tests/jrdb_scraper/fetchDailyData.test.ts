import { describe, it, expect, vi, beforeEach, afterAll, beforeAll } from 'vitest'
import { readFileSync, existsSync } from 'fs'
import { join } from 'path'
import firebaseFunctionsTest from 'firebase-functions-test'
import { initializeApp } from 'firebase-admin/app'
import { fetchDailyData } from '../../src/jrdb_scraper/fetchDailyData'
import { handleFetchJRDBDailyData } from '../../src/jrdb_scraper/handlers'
import { JRDBDataType } from '../../src/jrdb_scraper/entities/jrdb'

vi.mock('../../src/jrdb_scraper/downloader', () => ({
  downloadJRDBFile: vi.fn()
}))


vi.mock('../../src/jrdb_scraper/fetchDailyData', () => ({
  fetchDailyData: vi.fn()
}))

vi.mock('../../src/utils/storageUploader', async () => {
  const fs = await import('fs')
  const path = await import('path')
  const os = await import('os')
  
  return {
    createTempDir: vi.fn(() => {
      const tempDir = path.join(os.tmpdir(), `jrdb-test-${Date.now()}`)
      fs.mkdirSync(tempDir, { recursive: true })
      return tempDir
    }),
    uploadFileToStorage: vi.fn()
  }
})

const testEnv = firebaseFunctionsTest()

// Firebase Admin SDKを初期化（エミュレータ接続用）
beforeAll(() => {
  process.env.FIRESTORE_EMULATOR_HOST = '127.0.0.1:8180'
  process.env.STORAGE_EMULATOR_HOST = '127.0.0.1:9198'
  try {
    initializeApp({
      projectId: 'umayomi-fbb2b'
    })
  } catch {
    // 既に初期化されている場合は無視
  }
})

describe('fetchDailyData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterAll(() => {
    testEnv.cleanup()
  })

  it('データが正しく取得され、Firestore、Storage（LZH/Parquet）、カスタムメタデータに保存される', async () => {
    const lzhFilePath = join(__dirname, '../../mock/jrdb/KYI251102.lzh')
    
    if (!existsSync(lzhFilePath)) {
      // eslint-disable-next-line no-console
      console.warn(`テストファイルが見つかりません: ${lzhFilePath}`)
      return
    }

    const { downloadJRDBFile } = await import('../../src/jrdb_scraper/downloader')
    const { uploadFileToStorage } = await import('../../src/utils/storageUploader')

    const lzhBuffer = readFileSync(lzhFilePath)
    const sourceUrl = 'https://jrdb.com/member/data/Kyi/KYI251102.lzh'
    
    // モック設定
    vi.mocked(downloadJRDBFile).mockResolvedValue(lzhBuffer)
    vi.mocked(uploadFileToStorage).mockResolvedValue(undefined)

    // fetchDailyDataを実行（配列で指定）
    const results = await fetchDailyData(2025, 11, 2, [JRDBDataType.KYI])
    const result = results[0]

    // 1. 基本結果の確認
    expect(result.success).toBe(true)
    expect(result.dataType).toBe('KYI')
    expect(result.recordCount).toBeGreaterThan(0)
    expect(result.lzhStoragePath).toBe('jrdb/lzh/KYI251102.lzh')
    expect(result.npzStoragePath).toBe('jrdb/npz/KYI251102.npz')
    expect(result.jsonStoragePath).toBe('jrdb/json/KYI251102.json')
    expect(result.fileName).toBe('KYI251102')

    // 2. Firestoreへの保存を確認
    const { getFirestore } = await import('firebase-admin/firestore')
    const db = getFirestore()
    const date = '2025-11-02'
    const metadataDoc = await db.collection('jrdb_daily_data').doc(date).collection('KYI').doc('metadata').get()
    expect(metadataDoc.exists).toBe(true)

    const metadata = metadataDoc.data()
    expect(metadata?.dataType).toBe('KYI')
    expect(metadata?.date).toBe(date)
    expect(metadata?.year).toBe(2025)
    expect(metadata?.month).toBe(11)
    expect(metadata?.day).toBe(2)
    expect(metadata?.lzhStoragePath).toBe('jrdb/lzh/KYI251102.lzh')
    expect(metadata?.npzStoragePath).toBe('jrdb/npz/KYI251102.npz')
    expect(metadata?.jsonStoragePath).toBe('jrdb/json/KYI251102.json')
    expect(metadata?.fileName).toBe('KYI251102')
    expect(metadata?.recordCount).toBeGreaterThan(0)

    // recordsコレクションの確認
    const recordsSnapshot = await db.collection('jrdb_daily_data').doc(date).collection('KYI').doc('metadata').collection('records').limit(1).get()
    expect(recordsSnapshot.size).toBeGreaterThan(0)

    const firstRecord = recordsSnapshot.docs[0].data()
    expect(firstRecord).toBeDefined()
    expect(firstRecord).toHaveProperty('レースキー')

    // 3. Storageへのファイル保存を確認（LZH, NPZ, JSON）
    expect(uploadFileToStorage).toHaveBeenCalledTimes(3)
    
    // LZHファイルの保存を確認
    const lzhCall = vi.mocked(uploadFileToStorage).mock.calls.find(call => 
      call[1] === 'jrdb/lzh/KYI251102.lzh'
    )
    expect(lzhCall).toBeDefined()
    expect(lzhCall?.[2]).toMatchObject({
      fileName: 'KYI251102',
      sourceUrl,
      dataType: 'KYI',
      date
    })
    
    // NPZファイルの保存を確認
    const npzCall = vi.mocked(uploadFileToStorage).mock.calls.find(call => 
      call[1] === 'jrdb/npz/KYI251102.npz'
    )
    expect(npzCall).toBeDefined()
    expect(npzCall?.[2]).toMatchObject({
      fileName: 'KYI251102',
      sourceUrl,
      dataType: 'KYI',
      date
    })
    
    // JSONファイルの保存を確認
    const jsonCall = vi.mocked(uploadFileToStorage).mock.calls.find(call => 
      call[1] === 'jrdb/json/KYI251102.json'
    )
    expect(jsonCall).toBeDefined()
    expect(jsonCall?.[2]).toMatchObject({
      fileName: 'KYI251102',
      sourceUrl,
      dataType: 'KYI',
      date
    })
  }, 60000)
})

describe('handleFetchJRDBDailyData', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterAll(() => {
    testEnv.cleanup()
  })

  it('正しいパラメータでリクエストされた場合、正常にレスポンスを返す', async () => {
    const mockRequest = {
      query: {
        year: '2025',
        month: '11',
        day: '2',
        dataType: 'BAC'
      }
    }

    const mockResponse = {
      status: vi.fn().mockReturnThis(),
      send: vi.fn()
    }

    const mockFetchDailyDataResult = [{
      date: '2025-11-02',
      dataType: 'BAC',
      success: true,
      recordCount: 24,
      lzhStoragePath: 'jrdb/lzh/BAC251102.lzh',
      npzStoragePath: 'jrdb/npz/BAC251102.npz',
      jsonStoragePath: 'jrdb/json/BAC251102.json',
      fileName: 'BAC251102'
    }]

    vi.mocked(fetchDailyData).mockResolvedValue(mockFetchDailyDataResult)

    await handleFetchJRDBDailyData(mockRequest as any, mockResponse as any)

    expect(fetchDailyData).toHaveBeenCalledWith(2025, 11, 2, [JRDBDataType.BAC])
    expect(mockResponse.status).not.toHaveBeenCalled()
    expect(mockResponse.send).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        message: 'BACデータの取得が完了しました（日付: 2025-11-02）',
        date: '2025-11-02',
        dataType: 'BAC',
        recordCount: 24,
        lzhStoragePath: 'jrdb/lzh/BAC251102.lzh',
        fileName: 'BAC251102',
        executionTimeMs: expect.any(Number)
      })
    )
  })
})

