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
router.beforeEach(async (to, from, next) => {
  // 認証が必要なページかチェック
  if (to.meta.requiresAuth) {
    // Firebase Authの現在のユーザーを確認
    const { getCurrentUser } = await import('./config/firebase')
    const currentUser = getCurrentUser()
    
    if (!currentUser) {
      // 未認証の場合はホームページにリダイレクト
      next('/')
      return
    }
  }
  
  next()
})

const app = createApp(App)

app.use(router)
app.use(PrimeVue, primeVueConfig)
app.use(ConfirmationService)
app.use(ToastService)

app.mount('#app')
