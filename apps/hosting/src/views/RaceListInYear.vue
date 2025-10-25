<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-4 sm:mb-6">
      <h1 class="text-2xl sm:text-3xl font-bold text-gray-900">競馬レース一覧</h1>
      <p class="text-sm sm:text-base text-gray-600 mt-1">開催月を選択してください</p>
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
    <div v-else-if="raceMonths.length === 0" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-surface-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-surface-900 mb-2">レースデータがありません</h3>
        <p class="text-surface-600">10月分のレースデータが見つかりませんでした。</p>
      </div>
    </div>

    <!-- 月一覧 -->
    <div v-else class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- カード表示 -->
      <div v-if="viewMode === 'card'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="month in raceMonths"
          :key="month.id"
          class="cursor-pointer hover:shadow-lg transition-shadow duration-200 rounded-xl overflow-hidden"
          @click="selectMonth(month)"
        >
          <template #header>
            <div class="bg-surface-900 text-surface-0 p-4 text-center">
              <h3 class="text-xl font-bold">{{ month.name }}</h3>
            </div>
          </template>
          <template #content>
            <div class="p-4">
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm text-surface-600">開催日数</span>
                <Chip :label="`${month.days.length}日`" severity="info" />
              </div>
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm text-surface-600">総レース数</span>
                <Chip :label="`${getTotalRaces(month)}レース`" severity="success" />
              </div>
              <div class="text-sm text-surface-500">
                <div v-for="day in month.days.slice(0, 3)" :key="day.id" class="mb-1">
                  {{ day.date }} - {{ day.venue }}
                </div>
                <div v-if="month.days.length > 3" class="text-surface-400">
                  ...他{{ month.days.length - 3 }}日
                </div>
              </div>
            </div>
          </template>
          <template #footer>
            <Button
              label="詳細を見る"
              icon="pi pi-arrow-right"
              class="w-full"
              @click.stop="selectMonth(month)"
            />
          </template>
        </Card>
      </div>

      <!-- DataTable表示 -->
      <div v-else>
        <DataTable 
          :value="raceMonths" 
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
          <Column field="name" header="月" :sortable="true">
            <template #body="slotProps">
              <div class="font-semibold">{{ slotProps.data.name }}</div>
              <div class="text-sm text-surface-600">開催日数: {{ slotProps.data.days.length }}日</div>
            </template>
          </Column>
          <Column field="days.length" header="開催日数" :sortable="true">
            <template #body="slotProps">
              <Chip :label="`${slotProps.data.days.length}日`" severity="info" size="small" />
            </template>
          </Column>
          <Column header="総レース数" :sortable="true">
            <template #body="slotProps">
              <Chip :label="`${getTotalRaces(slotProps.data)}レース`" severity="success" size="small" />
            </template>
          </Column>
          <Column header="アクション" :exportable="false">
            <template #body="slotProps">
              <Button
                label="詳細"
                icon="pi pi-arrow-right"
                size="small"
                @click="selectMonth(slotProps.data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
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
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const { navigateTo, navigateTo404 } = useNavigation()
const { races, loading, error, fetchOctoberRaces } = useRace()

const viewMode = ref<'card' | 'list'>('card')

// レースデータを月ごとにグループ化
const raceMonths = computed(() => {
  const grouped: { [key: string]: { id: string, name: string, year: number, month: number, days: any[] } } = {}
  
  races.value.forEach((race: Race) => {
    const raceDate = race.date instanceof Date ? race.date : (race.date as any).toDate()
    const year = raceDate.getFullYear()
    const month = raceDate.getMonth() + 1
    const day = raceDate.getDate()
    
    const monthId = `${year}-${month}`
    const dayId = `${year}-${month}-${day}`
    
    if (!grouped[monthId]) {
      grouped[monthId] = {
        id: monthId,
        name: `${year}年${month}月`,
        year,
        month,
        days: []
      }
    }
    
    // 日付ごとにグループ化
    let dayData = grouped[monthId].days.find(d => d.id === dayId)
    if (!dayData) {
      dayData = {
        id: dayId,
        date: `${year}年${month}月${day}日`,
        venue: race.racecourse,
        races: []
      }
      grouped[monthId].days.push(dayData)
    }
    
    dayData.races.push(race)
  })
  
  return Object.values(grouped).sort((a, b) => {
    if (a.year !== b.year) return a.year - b.year
    return a.month - b.month
  })
})

const getTotalRaces = (month: any) => {
  return month.days.reduce((total: number, day: any) => total + day.races.length, 0)
}

const selectMonth = (month: any) => {
  // 月IDから年と月を抽出（例: "2024-10" -> year: 2024, month: 10）
  const [year, monthNum] = month.id.split('-')
  const yearNum = parseInt(year)
  const monthNumber = parseInt(monthNum)
  
  if (isNaN(yearNum) || isNaN(monthNumber)) {
    navigateTo404()
    return
  }
  
  navigateTo(RouteName.RACE_LIST_IN_MONTH, { year: yearNum, month: monthNumber })
}

onMounted(async () => {
  await fetchOctoberRaces()
})
</script>
