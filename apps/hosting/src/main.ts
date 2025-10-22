import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import PrimeVue from 'primevue/config'
import ConfirmationService from 'primevue/confirmationservice'

import App from './App.vue'
import routes from './router'
import { primeVueConfig } from './config/primevue'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

app.use(router)
app.use(PrimeVue, primeVueConfig)
app.use(ConfirmationService)

app.mount('#app')
