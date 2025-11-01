import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import 'primeflex/primeflex.css'

import App from './App.vue'
import routes from './router'
import { primeVueConfig } from './config/primevue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 認証ガード
router.beforeEach(async (to: any, _from: any, next: any) => {
  // 認証が必要でない場合は通過
  if (!to.meta.requiresAuth) {
    next()
    return
  }

  // Firebase Authの初期化を待機
  const { onAuthStateChanged, auth, getGoogleRedirectResult } = await import('./config/firebase')
  
  // まずGoogleリダイレクト結果をチェック（リダイレクト後の場合）
  try {
    const redirectResult = await getGoogleRedirectResult()
    if (redirectResult.user) {
      // リダイレクトログイン成功後は認証状態が更新されるまで少し待つ
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  } catch (error) {
    console.error('リダイレクト結果の取得エラー:', error)
  }
  
  // 現在の認証状態を即座にチェック
  if (auth.currentUser) {
    // 既に認証済みの場合は通過
    if (!to.meta.requiresAdmin) {
      next()
      return
    }
    // 管理者権限チェック（一時的にスキップ）
    next()
    return
  }
  
  // 認証状態が確定していない場合は、認証状態の変更を待機
  return new Promise((resolve) => {
    let unsubscribe: (() => void) | null = null
    
    // タイムアウトを設定（5秒）
    const timeout = setTimeout(() => {
      if (unsubscribe) unsubscribe()
      // タイムアウト時はホームページにリダイレクト
      next('/')
      resolve(false)
    }, 5000)
    
    unsubscribe = onAuthStateChanged(auth, (currentUser: any) => {
      clearTimeout(timeout)
      if (unsubscribe) unsubscribe() // 一度だけ実行するために購読を解除
      
      // 未認証の場合はホームページにリダイレクト
      if (!currentUser) {
        next('/')
        resolve(false)
        return
      }

      // 管理者権限が必要でない場合は通過
      if (!to.meta.requiresAdmin) {
        next()
        resolve(true)
        return
      }

      // 一時的に管理者権限チェックを完全に無効化（初期設定用）
      // TODO: 本番環境では管理者権限チェックを有効化する
      next()
      resolve(true)
    })
  })
})

const app = createApp(App)

app.use(router)
app.use(PrimeVue, primeVueConfig)
app.use(ConfirmationService)
app.use(ToastService)
app.directive('tooltip', Tooltip)

app.mount('#app')
