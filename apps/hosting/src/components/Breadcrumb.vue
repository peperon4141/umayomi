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
import { placeCodeToVenue } from '../../../shared/venue'

const route = useRoute()

// race_keyから情報を抽出する関数
// race_key形式: 場コード_回_日目_R（例: "05_5_8_01"）
const parseRaceKey = (raceKey: string) => {
  const parts = raceKey.split('_')
  if (parts.length === 4) {
    const [placeCode, round, day, raceNumber] = parts
    return {
      round: parseInt(round),
      day: parseInt(day),
      raceNumber: parseInt(raceNumber),
      placeCode,
      placeName: placeCodeToVenue(placeCode)
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
  
  // レースリストページ
  if (route.path === '/race-list') {
    items.push({ label: 'レースリスト', url: '/race-list' })
  }
  // 直接レース詳細ページ
  else if (route.path.startsWith('/race/year/')) {
    const raceKey = route.params.raceId as string
    const year = parseInt(route.params.year as string)
    if (isNaN(year)) throw new Error(`Invalid year param: ${route.params.year}`)
    const raceInfo = parseRaceKey(raceKey)
    
    // レースリスト
    items.push({ label: 'レースリスト', url: '/race-list' })
    
    if (raceInfo) {
      // レース詳細（競馬場名とレース番号を表示）
      items.push({ 
        label: `${raceInfo.placeName} - ${raceInfo.raceNumber}R`, 
        url: generateRoute(RouteName.RACE_DETAIL_DIRECT, { year, raceId: raceKey })
      })
    } else {
      // パースできない場合はrace_keyをそのまま表示
      items.push({ 
        label: `レース: ${raceKey}`, 
        url: generateRoute(RouteName.RACE_DETAIL_DIRECT, { year, raceId: raceKey })
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
