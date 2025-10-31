<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-surface-900">{{ monthName }}</h1>
      <p class="text-surface-600 mt-1">開催日を選択してください</p>
    </div>

    <!-- 日付一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="day in raceDays"
          :key="day.id"
          class="cursor-pointer hover:shadow-lg transition-shadow duration-200 rounded-xl overflow-hidden"
          @click="selectDate(day)"
        >
          <template #header>
            <div class="bg-surface-900 text-surface-0 p-4 text-center">
              <h3 class="text-lg font-bold">{{ day.date }}</h3>
              <p class="text-sm opacity-90">{{ day.venue }}</p>
            </div>
          </template>
          <template #content>
            <div class="p-4">
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm text-surface-600">レース数</span>
                <Chip :label="`${day.races.length}レース`" severity="info" />
              </div>
              <div class="space-y-2">
                <div v-for="race in day.races.slice(0, 3)" :key="race.id" class="text-xs space-y-1">
                  <div class="flex justify-between items-center">
                    <span class="font-medium text-sm">{{ race.raceNumber }}R</span>
                    <span class="text-surface-600 text-xs">{{ race.raceName }}</span>
                  </div>
                  <div class="text-surface-700 text-xs">{{ race.raceName }}</div>
                  <div class="flex gap-1 flex-wrap">
                    <Chip v-if="race.grade" :label="race.grade" size="small" :severity="getGradeSeverity(race.grade)" class="text-xs" />
                    <Chip :label="`${race.distance}m`" size="small" severity="secondary" class="text-xs" />
                    <Chip :label="race.surface" size="small" severity="contrast" class="text-xs" />
                  </div>
                </div>
                <div v-if="day.races.length > 3" class="text-surface-400 text-sm">
                  ...他{{ day.races.length - 3 }}レース
                </div>
              </div>
            </div>
          </template>
          <template #footer>
            <Button
              label="レース一覧を見る"
              icon="pi pi-arrow-right"
              class="w-full"
              @click="selectDate(day)"
            />
          </template>
        </Card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import { useRace } from '@/composables/useRace'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { RouteName } from '@/router/routeCalculator'

const { navigateTo, getParams } = useNavigation()
const { races, fetchOctoberRaces } = useRace()

const monthName = ref('')

// レースデータを日付ごとにグループ化
const raceDays = computed(() => {
  const grouped: { [key: string]: { id: string, date: string, venue: string, races: Race[] } } = {}
  
  races.value.forEach((race: Race) => {
    const raceDate = race.date instanceof Date ? race.date : (race.date as any).toDate()
    const year = raceDate.getFullYear()
    const month = raceDate.getMonth() + 1
    const day = raceDate.getDate()
    
    const dayId = `${year}-${month}-${day}`
    const dateStr = `${year}年${month}月${day}日`
    
    if (!grouped[dayId]) {
      grouped[dayId] = {
        id: dayId,
        date: dateStr,
        venue: race.racecourse,
        races: []
      }
    }
    
    grouped[dayId].races.push(race)
  })
  
  return Object.values(grouped).sort((a, b) => a.id.localeCompare(b.id))
})


const selectDate = (day: any) => {
  // ルートパラメータから年と月を取得
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam) {
    navigateTo(RouteName.HOME)
    return
  }
  
  // 次の戦でparse
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  
  // parseに失敗した場合は404ページに飛ぶ
  if (isNaN(year) || isNaN(month)) {
    navigateTo(RouteName.HOME)
    return
  }
  
  // 日付を選択した時は、その日の日付専用ページに遷移
  const dayNumber = parseInt(day.id.split('-')[2]) // day.idから日付を取得
  navigateTo(RouteName.RACE_LIST_IN_DAY, { year, month, day: dayNumber })
}

const getGradeSeverity = (grade: string | undefined) => {
  if (!grade) return 'secondary'
  switch (grade) {
    case 'GⅠ': return 'danger'
    case 'GⅡ': return 'warning'
    case 'GⅢ': return 'info'
    case 'オープン': return 'success'
    default: return 'secondary'
  }
}



onMounted(async () => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam) {
    navigateTo(RouteName.HOME)
    return
  }
  
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  
  if (isNaN(year) || isNaN(month)) {
    navigateTo(RouteName.HOME)
    return
  }
  
  monthName.value = `${year}年${month}月`
  
  // Firestoreからレースデータを取得
  await fetchOctoberRaces()
})
</script>
