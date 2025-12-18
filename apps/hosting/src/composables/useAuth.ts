import { ref, onMounted, onUnmounted, computed } from 'vue'
import { 
  loginWithEmail, 
  registerWithEmail, 
  logout, 
  getCurrentUser, 
  onAuthChange,
  loginWithGoogle,
  getGoogleRedirectResult
} from '@/config/firebase'
import type { User } from 'firebase/auth'

export function useAuth() {
  const user = ref<User | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  // 認証状態の監視
  let unsubscribe: (() => void) | null = null

  onMounted(async () => {
    // リダイレクト結果をチェック
    try {
      const redirectResult = await getGoogleRedirectResult()
      if (redirectResult.error) error.value = redirectResult.error
    } catch (err: any) {
      error.value = err?.message ?? 'リダイレクト結果の取得に失敗しました'
    }

    unsubscribe = onAuthChange(async (authUser) => {
      user.value = authUser
      loading.value = false
      
      // カスタムクレームを更新するためにIDトークンを再取得
      if (authUser) {
        try {
          await authUser.getIdToken(true) // 強制的にトークンを更新
        } catch {}
      }
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

  // ユーザーのロールを取得
  const getUserRole = () => {
    const currentUser = getCurrentUser()
    if (!currentUser) return null
    
    // カスタムクレームからロールを取得
    const claims = (currentUser as any).customClaims
    return claims?.role || 'user'
  }

  // 管理者かどうかをチェック（リアクティブ）
  const isAdmin = computed(() => {
    if (!user.value) return false
    // 一時的に管理者権限を有効化（初期設定用）
    // TODO: 本番環境では適切な管理者権限チェックを実装する
    return true
    // return getUserRole() === 'admin'
  })

  // ユーザーが特定のロールを持っているかチェック
  const hasRole = (role: string) => {
    return getUserRole() === role
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
    clearError,
    getUserRole,
    isAdmin,
    hasRole
  }
}
