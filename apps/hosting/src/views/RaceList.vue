<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ raceDay?.date }}</h1>
      <p class="text-gray-600 mt-1">{{ raceDay?.venue }} - {{ raceDay?.races.length }}レース</p>
    </div>

    <!-- 表示切り替えボタン -->
    <div class="mb-6 flex justify-end">
      <div class="flex bg-surface-100 rounded-lg p-1">
        <Button
          :class="{ 'bg-surface-0 shadow-sm': viewMode === 'card' }"
          icon="pi pi-th-large"
          @click="viewMode = 'card'"
          text
          rounded
        />
        <Button
          :class="{ 'bg-surface-0 shadow-sm': viewMode === 'list' }"
          icon="pi pi-list"
          @click="viewMode = 'list'"
          text
          rounded
        />
      </div>
    </div>

    <!-- レース一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- カード表示 -->
      <div v-if="viewMode === 'card'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="race in raceDay?.races"
          :key="race.id"
          class="cursor-pointer hover:shadow-lg transition-shadow duration-200 rounded-xl overflow-hidden"
          @click="selectRace(race)"
        >
          <template #header>
            <div class="bg-surface-900 text-surface-0 p-4 text-center">
              <h3 class="text-lg font-bold">{{ race.raceNumber }}R</h3>
              <p class="text-sm opacity-90">{{ race.startTime }}</p>
            </div>
          </template>
          <template #content>
            <div class="p-4">
              <div class="mb-3">
                <h4 class="font-bold text-lg text-surface-900 mb-2">{{ race.raceName }}</h4>
                <div class="flex flex-wrap gap-2 mb-3">
                  <Chip :label="race.grade" severity="contrast" />
                  <Chip :label="`${race.distance}m`" severity="contrast" />
                  <Chip :label="race.surface" severity="contrast" />
                </div>
              </div>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-surface-600">賞金</span>
                  <span class="font-medium">{{ formatPrize(race.prize) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-surface-600">競馬場</span>
                  <span class="font-medium">{{ race.venue }}</span>
                </div>
                <div class="text-surface-500 text-xs mt-2">
                  {{ race.description }}
                </div>
              </div>
            </div>
          </template>
          <template #footer>
            <Button
              label="詳細を見る"
              icon="pi pi-arrow-right"
              class="w-full"
              @click="selectRace(race)"
            />
          </template>
        </Card>
      </div>

      <!-- リスト表示 -->
      <div v-else class="space-y-4">
        <div
          v-for="race in raceDay?.races"
          :key="race.id"
          class="bg-surface-0 border border-surface-200 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow duration-200"
          @click="selectRace(race)"
        >
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold text-surface-900">{{ race.raceNumber }}R {{ race.raceName }}</h3>
              <p class="text-sm text-surface-600">{{ race.startTime }} - {{ race.venue }}</p>
            </div>
            <div class="flex items-center space-x-4">
              <Chip :label="`${race.distance}m`" severity="info" />
              <Chip :label="race.grade" :severity="getGradeSeverity(race.grade)" />
              <span class="text-sm font-medium">{{ formatPrize(race.prize) }}</span>
              <Button
                label="詳細を見る"
                icon="pi pi-arrow-right"
                size="small"
                @click.stop="selectRace(race)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import AppLayout from '@/layouts/AppLayout.vue'
import { mockRaceMonths } from '@/utils/mockData'
import type { Race, RaceDay } from '@/utils/mockData'
import { RouteName } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'

const { navigateTo, navigateTo404, getParams } = useNavigation()

const raceDay = ref<RaceDay | null>(null)
const viewMode = ref<'card' | 'list'>('card')
const monthName = ref('')



const formatPrize = (prize: number) => {
  if (prize >= 1000000) {
    return `${(prize / 1000000).toFixed(0)}万円`
  } else if (prize >= 1000) {
    return `${(prize / 1000).toFixed(0)}千円`
  } else {
    return `${prize}円`
  }
}

const getGradeSeverity = (grade: string) => {
  switch (grade) {
    case 'GⅠ': return 'danger'
    case 'GⅡ': return 'warning'
    case 'GⅢ': return 'info'
    case 'オープン': return 'success'
    default: return 'secondary'
  }
}

const selectRace = (race: Race) => {
  // ルートパラメータから年、月、場所を取得
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const placeId = params.placeId
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam || !placeId) {
        navigateTo404()
    return
  }
  
  // 次の戦でparse
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  
  // parseに失敗した場合は404ページに飛ぶ
  if (isNaN(year) || isNaN(month)) {
        navigateTo404()
    return
  }
  
  navigateTo(RouteName.RACE_DETAIL, { year, month, placeId, raceId: race.id })
}


onMounted(() => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const placeId = params.placeId
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam || !placeId) {
        navigateTo404()
    return
  }
  
  // 該当する月から該当する日付を検索
  const monthId = `${yearParam}-${monthParam}`
  const monthData = mockRaceMonths.find(m => m.id === monthId)
  
  if (monthData) {
    const day = monthData.days.find(d => d.id === placeId)
    if (day) {
      raceDay.value = day
      monthName.value = monthData.name
    } else {
      navigateTo(RouteName.RACE_LIST_IN_YEAR, { year: new Date().getFullYear() })
    }
  } else {
    navigateTo(RouteName.RACE_LIST_IN_YEAR, { year: 2024 })
  }
})
</script>
