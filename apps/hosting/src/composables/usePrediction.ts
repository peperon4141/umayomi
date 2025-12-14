import { ref, computed } from 'vue'
import { collection, doc, getDoc, query, orderBy, limit, getDocs, Timestamp } from 'firebase/firestore'
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

  const getPredictionsByDate = async (date: string): Promise<PredictionDocument | null> => {
    loading.value = true
    error.value = null

    try {
      const docId = `date_${date.replace(/-/g, '_')}`
      const docRef = doc(db, 'predictions', docId)
      const docSnap = await getDoc(docRef)

      if (docSnap.exists()) {
        const data = docSnap.data() as PredictionDocument
        predictions.value = data.predictions || []
        return data
      } else {
        predictions.value = []
        return null
      }
    } catch (err: any) {
      error.value = err.message || '予測結果の取得に失敗しました'
      predictions.value = []
      return null
    } finally {
      loading.value = false
    }
  }

  const getPredictionsByRaceKey = (raceKey: string): Prediction[] => {
    return predictions.value.filter(p => p.race_key === raceKey)
      .sort((a, b) => a.predicted_rank - b.predicted_rank)
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
      error.value = err.message || '予測結果の取得に失敗しました'
      return []
    } finally {
      loading.value = false
    }
  }

  return {
    predictions: computed(() => predictions.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    getPredictionsByDate,
    getPredictionsByRaceKey,
    getRecentPredictions
  }
}

