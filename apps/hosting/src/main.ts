import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'
import ToastService from 'primevue/toastservice'

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
  const { onAuthStateChanged, auth } = await import('./config/firebase')
  
  // 認証状態の変更を待機
  return new Promise((resolve) => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser: any) => {
      unsubscribe() // 一度だけ実行するために購読を解除
      
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
      console.log('管理者権限チェックをスキップ:', to.path)
      console.log('管理画面にアクセス許可:', to.path)
      next()
      resolve(true)
      return

    })
  })
})

const app = createApp(App)

app.use(router)
app.use(PrimeVue, primeVueConfig)
app.use(ConfirmationService)
app.use(ToastService)

app.mount('#app')
