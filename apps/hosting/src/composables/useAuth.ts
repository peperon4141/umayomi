import { ref, onMounted, onUnmounted } from 'vue'
import { 
  loginWithEmail, 
  registerWithEmail, 
  logout, 
  getCurrentUser, 
  onAuthChange,
  loginWithGoogle
} from '@/config/firebase'
import type { User } from 'firebase/auth'

export function useAuth() {
  const user = ref<User | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  // 認証状態の監視
  let unsubscribe: (() => void) | null = null

  onMounted(() => {
    unsubscribe = onAuthChange((authUser) => {
      user.value = authUser
      loading.value = false
    })
  })

  onUnmounted(() => {
    if (unsubscribe) {
      unsubscribe()
    }
  })

  // メール認証でログイン
  const login = async (email: string, password: string) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await loginWithEmail(email, password)
      if (result.error) {
        error.value = result.error
        return false
      }
      return true
    } catch (err: any) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  // メール認証で新規登録
  const register = async (email: string, password: string) => {
    loading.value = true
    error.value = null
    
    try {
      const result = await registerWithEmail(email, password)
      if (result.error) {
        error.value = result.error
        return false
      }
      return true
    } catch (err: any) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  // Google認証でログイン
  const loginWithGoogleAuth = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await loginWithGoogle()
      if (result.error) {
        error.value = result.error
        return false
      }
      return true
    } catch (err: any) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  // ログアウト
  const signOut = async () => {
    loading.value = true
    error.value = null
    
    try {
      const result = await logout()
      if (result.error) {
        error.value = result.error
        return false
      }
      return true
    } catch (err: any) {
      error.value = err.message
      return false
    } finally {
      loading.value = false
    }
  }

  // 現在のユーザーを取得
  const getCurrentUserInfo = () => {
    return getCurrentUser()
  }

  // エラーをクリア
  const clearError = () => {
    error.value = null
  }

  return {
    user,
    loading,
    error,
    login,
    register,
    loginWithGoogleAuth,
    signOut,
    getCurrentUserInfo,
    clearError
  }
}
