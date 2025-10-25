<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-4 sm:mb-6">
      <h1 class="text-2xl sm:text-3xl font-bold text-surface-900">{{ dayName }}</h1>
      <p class="text-sm sm:text-base text-surface-600 mt-1">その日のレース一覧</p>
    </div>

    <!-- 表示切り替えボタン -->
    <div class="mb-4 sm:mb-6 flex justify-end">
      <div class="flex bg-surface-100 rounded-lg p-1">
        <Button
          :class="{ 'bg-surface-0 shadow-sm': viewMode === 'card' }"
          icon="pi pi-th-large"
          @click="viewMode = 'card'"
          text
          rounded
          size="small"
        />
        <Button
          :class="{ 'bg-surface-0 shadow-sm': viewMode === 'list' }"
          icon="pi pi-list"
          @click="viewMode = 'list'"
          text
          rounded
          size="small"
        />
      </div>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <i class="pi pi-spin pi-spinner text-4xl text-surface-500 mb-4"></i>
        <p class="text-surface-600">レースデータを読み込み中...</p>
      </div>
    </div>

    <!-- エラー -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <i class="pi pi-exclamation-triangle text-red-500 text-4xl mb-4"></i>
        <h3 class="text-red-800 font-medium mb-2">エラーが発生しました</h3>
        <p class="text-red-600">{{ error }}</p>
      </div>
    </div>

    <!-- データなし -->
    <div v-else-if="dayRaces.length === 0" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-surface-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-surface-900 mb-2">レースデータがありません</h3>
        <p class="text-surface-600">指定された日のレースが見つかりませんでした。</p>
      </div>
    </div>

    <!-- レース一覧 -->
    <div v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- カード表示 -->
      <div v-if="viewMode === 'card'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="race in dayRaces"
          :key="race.id"
          class="cursor-pointer hover:shadow-lg transition-shadow duration-200 rounded-xl overflow-hidden"
          @click="selectRace(race)"
        >
          <template #header>
            <div class="bg-surface-900 text-surface-0 p-4 text-center">
              <h3 class="text-lg font-bold">{{ race.raceName }}</h3>
              <p class="text-sm opacity-90">{{ race.racecourse }}</p>
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
                <span class="text-sm text-surface-600">発走時刻</span>
                <span class="text-sm font-medium">{{ race.raceName }}</span>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- DataTable表示 -->
      <div v-else>
        <DataTable 
          :value="dayRaces" 
          :paginator="true" 
          :rows="10"
          :rowsPerPageOptions="[5, 10, 20]"
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
          currentPageReportTemplate="全 {totalRecords} 件中 {first} 〜 {last} 件を表示"
          responsiveLayout="scroll"
          :scrollable="true"
          scrollHeight="400px"
          class="p-datatable-sm"
        >
          <Column field="raceName" header="レース名" :sortable="true">
            <template #body="slotProps">
              <div class="font-semibold">{{ slotProps.data.raceName }}</div>
              <div class="text-sm text-surface-600">{{ slotProps.data.racecourse }}</div>
            </template>
          </Column>
          <Column field="distance" header="距離" :sortable="true">
            <template #body="slotProps">
              <Chip :label="`${slotProps.data.distance}m`" severity="info" size="small" />
            </template>
          </Column>
          <Column field="grade" header="グレード" :sortable="true">
            <template #body="slotProps">
              <Chip :label="slotProps.data.grade" :severity="getGradeSeverity(slotProps.data.grade)" size="small" />
            </template>
          </Column>
          <Column field="raceName" header="レース名" :sortable="true">
            <template #body="slotProps">
              <span class="font-medium">{{ slotProps.data.raceName }}</span>
            </template>
          </Column>
          <Column header="アクション" :exportable="false">
            <template #body="slotProps">
              <Button
                label="詳細"
                icon="pi pi-arrow-right"
                size="small"
                @click="selectRace(slotProps.data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import { useRace } from '@/composables/useRace'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { convertVenueToId } from '@/router/routeCalculator'
import { getVenueNameFromId } from '@/entity'
import { RouteName } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Chip from 'primevue/chip'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const { navigateTo, navigateTo404, getParams, getQuery } = useNavigation()
const { races, loading, error, fetchOctoberRaces } = useRace()

const dayRaces = ref<Race[]>([])
const dayName = ref('')
const viewMode = ref<'card' | 'list'>('card')

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
const loadDayRaces = async (year: number, month: number, day: number) => {
  try {
    await fetchOctoberRaces()
    
    // 指定された日付のレースをフィルタリング
    const filteredRaces = races.value.filter(race => {
      const raceDate = race.date instanceof Date ? race.date : (race.date as any).toDate()
      return raceDate.getFullYear() === year && 
             raceDate.getMonth() === month - 1 && 
             raceDate.getDate() === day
    })
    
    if (filteredRaces.length > 0) {
      dayName.value = `${year}年${month}月${day}日`
      dayRaces.value = filteredRaces
    } else {
      navigateTo404()
    }
  } catch (err) {
    console.error('レースデータの取得に失敗しました:', err)
    navigateTo404()
  }
}

// その日の特定競馬場のレースデータを取得
const loadDayRacesByPlace = async (year: number, month: number, day: number, placeId: string) => {
  try {
    await fetchOctoberRaces()
    
    // 指定された日付と競馬場のレースをフィルタリング
    const filteredRaces = races.value.filter(race => {
      const raceDate = race.date instanceof Date ? race.date : (race.date as any).toDate()
      const venueId = convertVenueToId(race.racecourse || '東京')
      return raceDate.getFullYear() === year && 
             raceDate.getMonth() === month - 1 && 
             raceDate.getDate() === day &&
             venueId === placeId
    })
    
    if (filteredRaces.length > 0) {
      dayName.value = `${year}年${month}月${day}日 - ${getVenueNameFromId(placeId as any)}`
      dayRaces.value = filteredRaces
    } else {
      navigateTo404()
    }
  } catch (err) {
    console.error('レースデータの取得に失敗しました:', err)
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
  
  const venueId = convertVenueToId(race.racecourse || '東京')
  navigateTo(RouteName.RACE_DETAIL, { year, month, placeId: venueId, raceId: race.id })
}


onMounted(async () => {
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
  
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  const day = parseInt(dayParam)
  
  if (isNaN(year) || isNaN(month) || isNaN(day)) {
    navigateTo404()
    return
  }
  
  // placeIdが指定されている場合は、その日のその競馬場のレース一覧を表示
  if (placeId) {
    await loadDayRacesByPlace(year, month, day, placeId as string)
  } else {
    // placeIdがない場合は、その日の全競馬場のレース一覧を表示
    await loadDayRaces(year, month, day)
  }
})
</script>
