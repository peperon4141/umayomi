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

      // カスタムクレームからロールを取得
      const claims = (currentUser as any).customClaims
      const userRole = claims?.role || 'user'
      
      // 管理者権限がない場合はダッシュボードにリダイレクト
      if (userRole !== 'admin') {
        next('/dashboard')
        resolve(false)
        return
      }

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

app.mount('#app')
