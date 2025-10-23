<template>
  <Breadcrumb :model="breadcrumbItems" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Breadcrumb from 'primevue/breadcrumb'

const route = useRoute()

// パスとdisplay nameのマップ
const pathDisplayMap: Record<string, string> = {
  '/': 'ホーム',
  '/races': 'レース一覧',
  '/dashboard': 'ダッシュボード',
  '/admin': '管理画面'
}

const breadcrumbItems = computed(() => {
  const items = [{ label: 'ホーム', route: '/' }]
  
  // 新しい階層構造に対応
  if (route.path.startsWith('/races')) {
    items.push({ label: 'レース一覧', route: '/races' })
    
    // 年
    if (route.params.year) {
      const year = route.params.year as string
      items.push({ label: `${year}年`, route: `/races/year/${year}` })
    }
    
    // 月
    if (route.params.month) {
      const year = route.params.year as string
      const month = route.params.month as string
      const monthNames = ['', '1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
      items.push({ 
        label: monthNames[parseInt(month)], 
        route: `/races/year/${year}/month/${month}` 
      })
    }
    
    // 場所（開催日）
    if (route.params.placeId) {
      const year = route.params.year as string
      const month = route.params.month as string
      const placeId = route.params.placeId as string
      items.push({ 
        label: `開催日: ${placeId}`, 
        route: `/races/year/${year}/month/${month}/place/${placeId}` 
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
        route: `/races/year/${year}/month/${month}/place/${placeId}/race/${raceId}` 
      })
    }
  } else if (pathDisplayMap[route.path]) {
    items.push({ label: pathDisplayMap[route.path], route: route.path })
  }
  
  return items
})
</script>
