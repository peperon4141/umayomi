<template>
  <div class="w-full overflow-hidden" style="white-space: nowrap; overflow-x: auto;">
    <Breadcrumb :model="breadcrumbItems" class="w-full" style="white-space: nowrap;" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  RouteName, 
  generateRoute
} from '@/router/routeCalculator'
import Breadcrumb from 'primevue/breadcrumb'

const route = useRoute()

// URLから年と月をパースする関数
const parseDateFromRaceId = (raceId: string) => {
  // raceIdの形式: "2025-10-19_東京_9"
  const match = raceId.match(/^(\d{4})-(\d{1,2})-(\d{1,2})_/)
  if (match) {
    return {
      year: parseInt(match[1]),
      month: parseInt(match[2]),
      day: parseInt(match[3])
    }
  }
  return null
}

// パスとdisplay nameのマップ
const pathDisplayMap: Record<string, string> = {
  '/': 'ホーム',
  '/dashboard': 'ダッシュボード',
  '/admin': '管理画面'
}

const breadcrumbItems = computed(() => {
  const items: any[] = []
  
  // レース関連の階層構造に対応
  if (route.path.startsWith('/races')) {
    items.push({ label: 'レースリスト', url: '/race-list' })
    
    // 日
    if (route.params.day) {
      const year = route.params.year as string
      const month = route.params.month as string
      const day = route.params.day as string
      items.push({ 
        label: `${day}日`, 
        url: generateRoute(RouteName.RACE_LIST_IN_DAY, {
          year: parseInt(year),
          month: parseInt(month),
          day: parseInt(day)
        })
      })
    }
    
    // 競馬場
    if (route.params.placeId) {
      const year = route.params.year as string
      const month = route.params.month as string
      const placeId = route.params.placeId as string
      items.push({ 
        label: `競馬場: ${placeId}`, 
        url: generateRoute(RouteName.RACE_LIST_IN_PLACE, { year: parseInt(year), month: parseInt(month), placeId })
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
        url: generateRoute(RouteName.RACE_DETAIL, { year: parseInt(year), month: parseInt(month), placeId, raceId })
      })
    }
  } 
  // 直接レース詳細ページ
  else if (route.path.startsWith('/race/')) {
    const raceId = route.params.raceId as string
    const dateInfo = parseDateFromRaceId(raceId)
    
    if (dateInfo) {
      // レースリスト
      items.push({ label: 'レースリスト', url: '/race-list' })
      
      // レース詳細
      items.push({ 
        label: 'レース詳細', 
        url: generateRoute(RouteName.RACE_DETAIL_DIRECT, { raceId })
      })
    } else {
      // パースできない場合は従来通り
      items.push({ 
        label: 'レース詳細', 
        url: generateRoute(RouteName.RACE_DETAIL_DIRECT, { raceId })
      })
    }
  }
  // その他のページ（ホーム以外）
  else if (pathDisplayMap[route.path] && route.path !== '/') {
    items.push({ label: pathDisplayMap[route.path], url: route.path })
  }
  
  return items
})
</script>
