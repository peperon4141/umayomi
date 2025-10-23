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
  
  // パスに応じてパンくずリストを生成
  if (route.path.startsWith('/races')) {
    items.push({ label: pathDisplayMap['/races'], route: '/races' })
    
    if (route.path.includes('/month/')) {
      const monthId = route.params.monthId as string
      items.push({ label: `月: ${monthId}`, route: `/races/month/${monthId}` })
    }
    
    if (route.path.includes('/date/')) {
      const dateId = route.params.dateId as string
      items.push({ label: `日: ${dateId}`, route: `/races/date/${dateId}` })
    }
    
    if (route.path.includes('/race/')) {
      const raceId = route.params.raceId as string
      items.push({ label: `レース: ${raceId}`, route: `/races/race/${raceId}` })
    }
  } else if (pathDisplayMap[route.path]) {
    items.push({ label: pathDisplayMap[route.path], route: route.path })
  }
  
  return items
})
</script>
