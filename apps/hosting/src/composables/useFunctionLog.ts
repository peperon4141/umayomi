import { ref, onMounted, onUnmounted } from 'vue'
import { 
  collection, 
  query, 
  orderBy, 
  limit, 
  onSnapshot, 
  Timestamp,
  type QueryConstraint 
} from 'firebase/firestore'
import { db } from '@/config/firebase'

export interface FunctionLog {
  id: string
  functionName: string
  timestamp: Date
  year: number
  month: number
  success: boolean
  message: string
  error?: string
  executionTimeMs?: number
  additionalData?: Record<string, any>
  createdAt: Date
}

export function useFunctionLog() {
  const logs = ref<FunctionLog[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  let unsubscribe: (() => void) | null = null

  const fetchFunctionLogs = async (limitCount: number = 50) => {
    loading.value = true
    error.value = null

    try {
      const constraints: QueryConstraint[] = [
        orderBy('timestamp', 'desc'),
        limit(limitCount)
      ]

      const q = query(collection(db, 'functions_log'), ...constraints)
      
      unsubscribe = onSnapshot(q, 
        (snapshot) => {
          logs.value = snapshot.docs.map(doc => {
            const data = doc.data()
            return {
              id: doc.id,
              functionName: data.functionName,
              timestamp: data.timestamp instanceof Timestamp ? data.timestamp.toDate() : data.timestamp,
              year: data.year,
              month: data.month,
              success: data.success,
              message: data.message,
              error: data.error,
              executionTimeMs: data.executionTimeMs,
              additionalData: data.additionalData || {},
              createdAt: data.createdAt instanceof Timestamp ? data.createdAt.toDate() : data.createdAt
            } as FunctionLog
          })
          loading.value = false
        },
        (err) => {
          error.value = err.message
          loading.value = false
        }
      )
    } catch (err: any) {
      error.value = err.message
      loading.value = false
    }
  }

  const stopListening = () => {
    if (unsubscribe) {
      unsubscribe()
      unsubscribe = null
    }
  }

  onMounted(() => {
    fetchFunctionLogs()
  })

  onUnmounted(() => {
    stopListening()
  })

  return {
    logs,
    loading,
    error,
    fetchFunctionLogs,
    stopListening
  }
}