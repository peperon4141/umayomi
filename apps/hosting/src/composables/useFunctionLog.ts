import { ref, computed } from 'vue'
import { collection, query, orderBy, limit, getDocs, getCountFromServer } from 'firebase/firestore'
import { db } from '@/config/firebase'

// ローカル型定義
interface FunctionLog {
  id: string
  functionName: string
  status: 'success' | 'failure'
  executedAt: any
  metadata?: {
    duration?: number
    errorMessage?: string
    responseData?: any
    method?: string
    url?: string
    [key: string]: any
  }
}

/**
 * Functions実行ログ管理用のComposable
 */
export function useFunctionLog() {
  const logs = ref<FunctionLog[]>([])
  const loading = ref(false)
  const totalCount = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(10)

  /**
   * ページネーション付きでログを取得
   */
  const fetchLogs = async (page: number = 1, size: number = 10) => {
    if (loading.value) return

    loading.value = true
    currentPage.value = page
    pageSize.value = size

    try {
      const logsCollection = collection(db, 'function_logs')
      
      // 総件数を取得
      const countSnapshot = await getCountFromServer(logsCollection)
      totalCount.value = countSnapshot.data().count

      // ページネーション用のクエリ（Firestore v9ではoffsetが利用できないため、startAfterを使用）
      const logsQuery = query(
        logsCollection,
        orderBy('executedAt', 'desc'),
        limit(size)
      )

      const snapshot = await getDocs(logsQuery)
      logs.value = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      } as FunctionLog))

    } catch (error) {
      console.error('Error fetching function logs:', error)
      logs.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * 総ページ数を計算
   */
  const totalPages = computed(() => {
    return Math.ceil(totalCount.value / pageSize.value)
  })

  /**
   * ページ変更時の処理
   */
  const onPageChange = (event: any) => {
    const newPage = (event.page || 0) + 1
    fetchLogs(newPage, pageSize.value)
  }

  /**
   * ログをリフレッシュ
   */
  const refreshLogs = () => {
    fetchLogs(currentPage.value, pageSize.value)
  }

  return {
    logs,
    loading,
    totalCount,
    currentPage,
    pageSize,
    totalPages,
    fetchLogs,
    onPageChange,
    refreshLogs
  }
}
