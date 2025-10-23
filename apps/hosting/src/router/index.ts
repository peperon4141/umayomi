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
  { path: '/races', name: 'RaceMonthList', component: RaceMonthList, meta: { requiresAuth: true } },
  { path: '/races/month/:monthId', name: 'RaceDateList', component: RaceDateList, meta: { requiresAuth: true } },
  { path: '/races/date/:dateId', name: 'RaceList', component: RaceList, meta: { requiresAuth: true } },
  { path: '/races/race/:raceId', name: 'RaceDetail', component: RaceDetail, meta: { requiresAuth: true } }
]

export default routes
