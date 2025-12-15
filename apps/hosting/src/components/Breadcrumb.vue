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
// race_key形式: 場コード_年_回_日_R（例: "07_25_1_1_15"）
const parseRaceKey = (raceKey: string) => {
  const parts = raceKey.split('_')
  if (parts.length >= 5) {
    const placeCode = parts[0]
    const year2Digit = parseInt(parts[1])
    const round = parts[2]
    const day = parts[3]
    const raceNumber = parts[4]
    
    // 2桁の年を4桁に変換（2000年代を想定）
    const year = 2000 + year2Digit
    
    return {
      year,
      month: null, // race_keyからは月が取得できない
      day: parseInt(day),
      round: parseInt(round),
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
  // 日付詳細ページ
  else if (route.path.startsWith('/races/year/') && route.params.day) {
    const year = route.params.year as string
    const month = route.params.month as string
    const day = route.params.day as string
    
    items.push({ label: 'レースリスト', url: '/race-list' })
    items.push({ 
      label: `${year}年${month}月${day}日`, 
      url: generateRoute(RouteName.RACE_LIST_IN_DAY, {
        year: parseInt(year),
        month: parseInt(month),
        day: parseInt(day)
      })
    })
  }
  // 直接レース詳細ページ
  else if (route.path.startsWith('/race/')) {
    const raceKey = route.params.raceId as string
    const raceInfo = parseRaceKey(raceKey)
    
    // レースリスト
    items.push({ label: 'レースリスト', url: '/race-list' })
    
    if (raceInfo) {
      // レース詳細（競馬場名とレース番号を表示）
      items.push({ 
        label: `${raceInfo.placeName} - ${raceInfo.raceNumber}R`, 
        url: generateRoute(RouteName.RACE_DETAIL_DIRECT, { raceId: raceKey })
      })
    } else {
      // パースできない場合はrace_keyをそのまま表示
      items.push({ 
        label: `レース: ${raceKey}`, 
        url: generateRoute(RouteName.RACE_DETAIL_DIRECT, { raceId: raceKey })
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
