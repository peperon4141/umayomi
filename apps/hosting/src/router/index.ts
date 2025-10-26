import { RouteRecordRaw } from 'vue-router'
import Home from '../views/Home.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import RaceListInYear from '../views/RaceListInYear.vue'
import RaceListInMonth from '../views/RaceListInMonth.vue'
import RaceList from '../views/RaceList.vue'
import RaceListInDay from '../views/RaceListInDay.vue'
import RaceDetail from '../views/RaceDetail.vue'
import NotFound from '../views/NotFound.vue'
import { 
  generateRoute,
  RouteName,
  getCurrentYear
} from './routeCalculator'

const routes: RouteRecordRaw[] = [
  { path: '/', name: RouteName.HOME, component: Home },
  { path: '/admin', name: RouteName.ADMIN_DASHBOARD, component: AdminDashboard, meta: { requiresAuth: true, requiresAdmin: true } },
  
  // レース詳細ページ（直接アクセス用）
  { path: '/race/:raceId', name: RouteName.RACE_DETAIL_DIRECT, component: RaceDetail, meta: { requiresAuth: true } },
  
  // 階層的なレース構造
  { path: '/races', redirect: generateRoute(RouteName.RACE_LIST_IN_YEAR, { year: getCurrentYear() }) },
  { path: '/races/year/:year', name: RouteName.RACE_LIST_IN_YEAR, component: RaceListInYear, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month', name: RouteName.RACE_LIST_IN_MONTH, component: RaceListInMonth, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/day/:day', name: RouteName.RACE_LIST_IN_DAY, component: RaceListInDay, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/place/:placeId', name: RouteName.RACE_LIST_IN_PLACE, component: RaceList, meta: { requiresAuth: true } },
  { path: '/races/year/:year/month/:month/place/:placeId/race/:raceId', name: RouteName.RACE_DETAIL, component: RaceDetail, meta: { requiresAuth: true } },
  
  // 404ページ（最後に配置）
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFound },
]

export default routes
