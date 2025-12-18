import { ref, computed, onUnmounted } from 'vue'
import { collection, doc, getDoc, query, orderBy, limit, getDocs, onSnapshot, Timestamp } from 'firebase/firestore'
import { db } from '../config/firebase'

export interface Prediction {
  race_key: string
  horse_number: number
  horse_name: string
  jockey_name: string
  trainer_name: string
  predicted_score: number
  predicted_rank: number
}

export interface PredictionDocument {
  date: string
  created_at: Timestamp
  updated_at: Timestamp
  predictions: Prediction[]
  total_count: number
}

export function usePrediction() {
  const predictions = ref<Prediction[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  let unsubscribe: (() => void) | null = null

  const getPredictionsByDate = async (date: string): Promise<PredictionDocument | null> => {
    loading.value = true
    error.value = null

    try {
      const docId = `date_${date.replace(/-/g, '_')}`
      const docRef = doc(db, 'predictions', docId)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        const data = docSnap.data() as PredictionDocument
        if (!Array.isArray(data.predictions)) throw new Error(`predictions field is missing or not an array: predictions/${docId}`)
        predictions.value = data.predictions
        return data
      } else {
        predictions.value = []
        return null
      }
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : '予測結果の取得に失敗しました'
      predictions.value = []
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 指定日の予測結果をリアルタイムで監視
   */
  const watchPredictionsByDate = (date: string): void => {
    // 既存のリスナーを解除
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }

    loading.value = true
    error.value = null

    try {
      const docId = `date_${date.replace(/-/g, '_')}`
      const docRef = doc(db, 'predictions', docId)

      unsubscribe = onSnapshot(
        docRef,
        (docSnap) => {
          if (docSnap.exists()) {
            const data = docSnap.data() as PredictionDocument
            if (!Array.isArray(data.predictions)) throw new Error(`predictions field is missing or not an array: predictions/${docId}`)
            predictions.value = data.predictions
            // デバッグ用ログ（開発環境のみ）
            if (import.meta.env.DEV) {
              const uniqueRaceKeys = [...new Set(data.predictions.map(p => p.race_key))]
              console.log(`[usePrediction] 予測結果を取得: ${data.predictions.length}件, ユニークrace_key: ${uniqueRaceKeys.length}件`, uniqueRaceKeys.slice(0, 10))
            }
          } else {
            predictions.value = []
            if (import.meta.env.DEV) {
              console.log(`[usePrediction] 予測結果ドキュメントが存在しません: predictions/${docId}`)
            }
          }
          loading.value = false
        },
        (err) => {
          error.value = err instanceof Error ? err.message : '予測結果の監視に失敗しました'
          predictions.value = []
          loading.value = false
        }
      )
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : '予測結果の監視に失敗しました'
      predictions.value = []
      loading.value = false
    }
  }

  /**
   * リアルタイム監視を停止
   */
  const stopWatching = (): void => {
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }
  }

  /**
   * race_keyで予測結果を取得（完全一致のみ）
   */
  const getPredictionsByRaceKey = (raceKey: string): Prediction[] => {
    const filtered = predictions.value.filter(p => p.race_key === raceKey)
      .sort((a, b) => a.predicted_rank - b.predicted_rank)
    // デバッグ用ログ（開発環境のみ）
    if (import.meta.env.DEV && filtered.length === 0 && predictions.value.length > 0) {
      const uniqueRaceKeys = [...new Set(predictions.value.map(p => p.race_key))]
      console.log(`[usePrediction] race_key一致なし: 検索race_key="${raceKey}", 利用可能なrace_key=${uniqueRaceKeys.slice(0, 10).join(', ')}`)
    }
    return filtered
  }

  const getRecentPredictions = async (limitCount: number = 10): Promise<PredictionDocument[]> => {
    loading.value = true
    error.value = null

    try {
      const q = query(
        collection(db, 'predictions'),
        orderBy('date', 'desc'),
        limit(limitCount)
      )
      const querySnapshot = await getDocs(q)
      
      const results: PredictionDocument[] = []
      querySnapshot.forEach((doc) => {
        results.push(doc.data() as PredictionDocument)
      })
      
      return results
    } catch (err: any) {
      error.value = err instanceof Error ? err.message : '予測結果の取得に失敗しました'
      return []
    } finally {
      loading.value = false
    }
  }

  // コンポーネントがアンマウントされたときにリスナーを解除
  onUnmounted(() => {
    stopWatching()
  })

  return {
    predictions: computed(() => predictions.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    getPredictionsByDate,
    getPredictionsByRaceKey,
    getRecentPredictions,
    watchPredictionsByDate,
    stopWatching
  }
}

