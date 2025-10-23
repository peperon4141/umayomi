import { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home.vue'
import Dashboard from '../views/Dashboard.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import RaceMonthList from '../views/RaceMonthList.vue'
import RaceDateList from '../views/RaceDateList.vue'
import RaceList from '../views/RaceList.vue'
import RaceDetail from '../views/RaceDetail.vue'


const routes: RouteRecordRaw[] = [
  { path: '/', name: 'Home', component: Home },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/admin', name: 'AdminDashboard', component: AdminDashboard, meta: { requiresAuth: true, requiresAdmin: true } },
  
  // レース詳細ページ（直接アクセス用）
  { path: '/race/:raceId', name: 'RaceDetailDirect', component: RaceDetail, meta: { requiresAuth: true } },
  
  // 階層的なレース構造
  { path: '/races', redirect: '/races/year/2024' },
  { path: '/races/year/:year', name: 'RaceMonthList', component: RaceMonthList, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month', name: 'RaceDateList', component: RaceDateList, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/place/:placeId', name: 'RaceList', component: RaceList, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/place/:placeId/race/:raceId', name: 'RaceDetail', component: RaceDetail, meta: { requiresAuth: true } },
  
  // 後方互換性のための旧ルート（リダイレクト用）
  { path: '/races/month/:monthId', redirect: to => `/races/year/2024/month/${to.params.monthId}` },
  { path: '/races/date/:dateId', redirect: to => `/races/year/2024/month/10/place/${to.params.dateId}` },
  { path: '/races/race/:raceId', redirect: to => `/races/year/2024/month/10/place/1/race/${to.params.raceId}` }
]

export default routes
