import { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import RaceListView from '../views/RaceListView.vue'
import RaceList from '../views/RaceList.vue'
import RaceListInDay from '../views/RaceListInDay.vue'
import RaceDetail from '../views/RaceDetail.vue'
import NotFound from '../views/NotFound.vue'
import { RouteName } from './routeCalculator'

const routes: RouteRecordRaw[] = [
  { path: '/', name: RouteName.HOME, component: Home },
  { path: '/admin', name: RouteName.ADMIN_DASHBOARD, component: AdminDashboard, meta: { requiresAuth: true, requiresAdmin: true } },
  
  // レースリストページ
  { path: '/race-list', name: RouteName.RACE_LIST, component: RaceListView, meta: { requiresAuth: true } },
  { path: '/races', redirect: '/race-list' },
  
  // レース詳細ページ（直接アクセス用）
  { path: '/race/:raceId', name: RouteName.RACE_DETAIL_DIRECT, component: RaceDetail, meta: { requiresAuth: true } },
  
  // 階層的なレース構造
  { path: '/races/year/:year/month/:month/day/:day', name: RouteName.RACE_LIST_IN_DAY, component: RaceListInDay, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/place/:placeId', name: RouteName.RACE_LIST_IN_PLACE, component: RaceList, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/place/:placeId/race/:raceId', name: RouteName.RACE_DETAIL, component: RaceDetail, meta: { requiresAuth: true } },
  
  // 404ページ（最後に配置）
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound },
]

export default routes
