<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-surface-900">{{ dayName }}</h1>
      <p class="text-surface-600 mt-1">その日のレース一覧</p>
    </div>

    <!-- レース一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="race in dayRaces"
          :key="race.id"
          class="cursor-pointer hover:shadow-lg transition-shadow duration-200 rounded-xl overflow-hidden"
          @click="selectRace(race)"
        >
          <template #header>
            <div class="bg-surface-900 text-surface-0 p-4 text-center">
              <h3 class="text-lg font-bold">{{ race.raceName }}</h3>
              <p class="text-sm opacity-90">{{ race.venue }}</p>
            </div>
          </template>
          <template #content>
            <div class="p-4">
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm text-surface-600">距離</span>
                <Chip :label="`${race.distance}m`" severity="info" />
              </div>
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm text-surface-600">グレード</span>
                <Chip :label="race.grade" :severity="getGradeSeverity(race.grade)" />
              </div>
              <div class="flex justify-between items-center">
                <span class="text-sm text-surface-600">賞金</span>
                <span class="text-sm font-medium">{{ formatPrize(race.prize) }}</span>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import AppLayout from '@/layouts/AppLayout.vue'
import { mockRaceMonths } from '@/utils/mockData'
import type { Race } from '@/utils/mockData'
import { convertVenueToId } from '@/router/routeCalculator'
import { getVenueNameFromId } from '@/entity'
import { RouteName } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Chip from 'primevue/chip'

const { navigateTo, navigateTo404, getParams, getQuery } = useNavigation()

const dayRaces = ref<Race[]>([])
const dayName = ref('')

const getGradeSeverity = (grade: string) => {
  switch (grade) {
    case 'GⅠ': return 'danger'
    case 'GⅡ': return 'warning'
    case 'GⅢ': return 'info'
    case 'オープン': return 'success'
    default: return 'secondary'
  }
}

// その日のレースデータを取得
const loadDayRaces = (year: number, month: number, day: number) => {
  const monthId = `${year}-${month}`
  const monthData = mockRaceMonths.find(m => m.id === monthId)
  
  if (monthData) {
    const dayData = monthData.days.find(d => d.id === `${year}-${month}-${day}`)
    if (dayData) {
      dayName.value = `${year}年${month}月${day}日`
      dayRaces.value = dayData.races
    } else {
        navigateTo404()
    }
  } else {
        navigateTo404()
  }
}

// その日の特定競馬場のレースデータを取得
const loadDayRacesByPlace = (year: number, month: number, day: number, placeId: string) => {
  const monthId = `${year}-${month}`
  const monthData = mockRaceMonths.find(m => m.id === monthId)
  
  if (monthData) {
    const dayData = monthData.days.find(d => d.id === `${year}-${month}-${day}`)
    if (dayData) {
      // 特定の競馬場のレースのみをフィルタリング
      const filteredRaces = dayData.races.filter(race => {
        const venueId = convertVenueToId(race.venue || '東京競馬場')
        return venueId === placeId
      })
      
      dayName.value = `${year}年${month}月${day}日 - ${getVenueNameFromId(placeId as any)}`
      dayRaces.value = filteredRaces
    } else {
        navigateTo404()
    }
  } else {
        navigateTo404()
  }
}

// レース選択時の処理
const selectRace = (race: Race) => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const dayParam = params.day
  
  if (!yearParam || !monthParam || !dayParam) {
          navigateTo404()
    return
  }
  
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  const day = parseInt(dayParam)
  
  if (isNaN(year) || isNaN(month) || isNaN(day)) {
          navigateTo404()
    return
  }
  
  const venueId = convertVenueToId(race.venue || '東京競馬場')
  navigateTo(RouteName.RACE_DETAIL, { year, month, placeId: venueId, raceId: race.id })
}

// 賞金フォーマット
const formatPrize = (prize: number) => {
  if (prize >= 10000) {
    return `${(prize / 10000).toFixed(0)}万円`
  }
  return `${prize.toLocaleString()}円`
}

onMounted(() => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const dayParam = params.day
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam || !dayParam) {
          navigateTo404()
    return
  }
  
  // クエリパラメータからplaceIdを取得
  const placeId = getQuery('placeId')
  
  // placeIdが指定されている場合は、その日のその競馬場のレース一覧を表示
  if (placeId) {
    const year = parseInt(yearParam)
    const month = parseInt(monthParam)
    const day = parseInt(dayParam)
    
    if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
      // その日のその競馬場のレースのみをフィルタリングして表示
      loadDayRacesByPlace(year, month, day, placeId as string)
      return
    }
  }
  
  // placeIdがない場合は、その日の全競馬場のレース一覧を表示
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  const day = parseInt(dayParam)
  
  if (!isNaN(year) && !isNaN(month) && !isNaN(day)) {
    // その日のレースデータを取得して表示
    loadDayRaces(year, month, day)
  } else {
          navigateTo404()
  }
})
</script>
