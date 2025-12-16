import { describe, it, expect, beforeEach, vi } from 'vitest'

// Firebase Admin SDKのモック
const mockBatch = {
  set: vi.fn(),
  commit: vi.fn().mockResolvedValue(undefined)
}

const mockDocRef = 'mock-doc-ref'

const mockCollection = {
  doc: vi.fn().mockReturnValue(mockDocRef)
}

const mockDb = {
  collection: vi.fn().mockReturnValue(mockCollection),
  batch: vi.fn().mockReturnValue(mockBatch)
}

vi.mock('firebase-admin/firestore', () => {
  return {
    getFirestore: vi.fn(() => mockDb)
  }
})

vi.mock('../../src/utils/raceKeyGenerator', () => {
  return {
    generateRaceKey: vi.fn((race: any) => {
      // roundがnullまたはundefinedの場合はエラーを投げる（fallbackを禁止）
      if (race.round == null) {
        throw new Error(`round is required but was null or undefined. raceDate: ${race.raceDate}, venue: ${race.venue || race.racecourse}, raceNumber: ${race.raceNumber}. Please ensure extractRound function correctly extracts round from JRA HTML.`)
      }
      
      // 簡単なrace_keyを生成
      const venue = race.venue || race.racecourse || '05'
      const year = race.raceDate ? new Date(race.raceDate).getFullYear() % 100 : 25
      const round = race.round
      const day = '1'
      const raceNumber = String(race.raceNumber || 1).padStart(2, '0')
      return `${venue}_${year}_${round}_${day}_${raceNumber}`
    })
  }
})

// モックの後にインポート
import { saveRacesToFirestore } from '../../src/utils/firestoreSaver'

describe('saveRacesToFirestore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // モックをリセット
    mockBatch.set.mockClear()
    mockBatch.commit.mockClear()
    mockDb.collection.mockClear()
    mockDb.batch.mockClear()
    mockCollection.doc.mockClear()
  })

  it('roundがnullのレースデータが含まれている場合はエラーを投げる（fallbackを禁止）', async () => {
    const races = [
      {
        raceNumber: 1,
        raceName: 'テストレース',
        venue: '東京',
        raceDate: new Date('2025-11-01'),
        round: null, // roundがnull
        distance: 1600,
        surface: '芝',
        raceStartTime: new Date('2025-11-01T09:50:00Z')
      }
    ]

    // roundがnullの場合、エラーが投げられることを確認
    await expect(async () => {
      await saveRacesToFirestore(races)
    }).rejects.toThrow(/round is required but was null or undefined/)
  })

  it('roundがundefinedのレースデータが含まれている場合はエラーを投げる（fallbackを禁止）', async () => {
    const races = [
      {
        raceNumber: 1,
        raceName: 'テストレース',
        venue: '東京',
        raceDate: new Date('2025-11-01'),
        // roundがundefined
        distance: 1600,
        surface: '芝',
        raceStartTime: new Date('2025-11-01T09:50:00Z')
      }
    ]

    // roundがundefinedの場合、エラーが投げられることを確認
    await expect(async () => {
      await saveRacesToFirestore(races)
    }).rejects.toThrow(/round is required but was null or undefined/)
  })

  it('venueがnullのレースデータが含まれている場合はエラーを投げる（fallbackを禁止）', async () => {
    const races = [
      {
        raceNumber: 1,
        raceName: 'テストレース',
        venue: null, // venueがnull
        raceDate: new Date('2025-11-01'),
        round: 1,
        distance: 1600,
        surface: '芝',
        raceStartTime: new Date('2025-11-01T09:50:00Z')
      }
    ]

    // venueがnullの場合、エラーが投げられることを確認
    await expect(async () => {
      await saveRacesToFirestore(races)
    }).rejects.toThrow(/venue or racecourse is required but both were null or undefined/)
  })

  it('raceDateがnullのレースデータが含まれている場合はエラーを投げる（fallbackを禁止）', async () => {
    const races = [
      {
        raceNumber: 1,
        raceName: 'テストレース',
        venue: '東京',
        raceDate: null, // raceDateがnull
        round: 1,
        distance: 1600,
        surface: '芝',
        raceStartTime: new Date('2025-11-01T09:50:00Z')
      }
    ]

    // raceDateがnullの場合、エラーが投げられることを確認
    await expect(async () => {
      await saveRacesToFirestore(races)
    }).rejects.toThrow(/raceDate or date is required but both were null or undefined/)
  })

  it('有効なレースデータは正常に保存される', async () => {
    const races = [
      {
        raceNumber: 1,
        raceName: 'テストレース',
        venue: '東京',
        raceDate: new Date('2025-11-01'),
        round: 1,
        distance: 1600,
        surface: '芝',
        raceStartTime: new Date('2025-11-01T09:50:00Z')
      }
    ]

    // エラーが投げられないことを確認
    await expect(async () => {
      await saveRacesToFirestore(races)
    }).not.toThrow()

    // batch.setが呼ばれたことを確認
    expect(mockBatch.set).toHaveBeenCalled()
    // batch.commitが呼ばれたことを確認
    expect(mockBatch.commit).toHaveBeenCalled()
  })
})
