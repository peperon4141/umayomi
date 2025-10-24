<template>
  <Breadcrumb :model="breadcrumbItems" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  RouteName, 
  generateRoute, 
  getCurrentYearRoute,
  getRaceYearRoute, 
  getRaceMonthRoute, 
  getRaceDateRoute, 
  getRaceDetailRoute 
} from '@/router/routeCalculator'
import Breadcrumb from 'primevue/breadcrumb'

const route = useRoute()
const router = useRouter()

// パスとdisplay nameのマップ
const pathDisplayMap: Record<string, string> = {
  '/': 'ホーム',
  '/dashboard': 'ダッシュボード',
  '/admin': '管理画面'
}

const breadcrumbItems = computed(() => {
  const items = [{ label: 'ホーム', command: () => router.push('/') }]
  
  // レース関連の階層構造に対応
  if (route.path.startsWith('/races')) {
    items.push({ label: 'レース一覧', command: () => router.push(getCurrentYearRoute()) })
    
    // 年
    if (route.params.year) {
      const year = route.params.year as string
      items.push({ 
        label: `${year}年`, 
        command: () => router.push(getRaceYearRoute(parseInt(year))) 
      })
    }
    
    // 月
    if (route.params.month) {
      const year = route.params.year as string
      const month = route.params.month as string
      const monthNames = ['', '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
      items.push({ 
        label: monthNames[parseInt(month)], 
        command: () => router.push(getRaceMonthRoute(parseInt(year), parseInt(month)))
      })
    }
    
    // 日
    if (route.params.day) {
      const year = route.params.year as string
      const month = route.params.month as string
      const day = route.params.day as string
      items.push({ 
        label: `${day}日`, 
        command: () => router.push(generateRoute(RouteName.RACE_LIST_IN_DAY, {
          year: parseInt(year),
          month: parseInt(month),
          day: parseInt(day)
        }))
      })
    }
    
    // 競馬場
    if (route.params.placeId) {
      const year = route.params.year as string
      const month = route.params.month as string
      const placeId = route.params.placeId as string
      items.push({ 
        label: `競馬場: ${placeId}`, 
        command: () => router.push(getRaceDateRoute(parseInt(year), parseInt(month), placeId))
      })
    }
    
    // レース
    if (route.params.raceId) {
      const year = route.params.year as string
      const month = route.params.month as string
      const placeId = route.params.placeId as string
      const raceId = route.params.raceId as string
      items.push({ 
        label: `レース: ${raceId}`, 
        command: () => router.push(getRaceDetailRoute(parseInt(year), parseInt(month), placeId, raceId))
      })
    }
  } 
  // 直接レース詳細ページ
  else if (route.path.startsWith('/race/')) {
    const raceId = route.params.raceId as string
    items.push({ 
      label: 'レース詳細', 
      command: () => router.push(generateRoute(RouteName.RACE_DETAIL_DIRECT, { raceId }))
    })
  }
  // その他のページ
  else if (pathDisplayMap[route.path]) {
    items.push({ label: pathDisplayMap[route.path], command: () => router.push(route.path) })
  }
  
  return items
})
</script>
