<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-4 sm:mb-6">
      <h1 class="text-2xl sm:text-3xl font-bold text-surface-900">{{ monthName }}</h1>
      <p class="text-sm sm:text-base text-surface-600 mt-1">開催日を選択してください</p>
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

    <!-- 日付一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- カード表示 -->
      <div v-if="viewMode === 'card'" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
                    <span class="text-surface-600 text-xs">{{ race.startTime }}</span>
                  </div>
                  <div class="text-surface-700 text-xs">{{ race.raceName }}</div>
                  <div class="flex gap-1 flex-wrap">
                    <Chip :label="race.grade" size="small" :severity="getGradeSeverity(race.grade)" class="text-xs" />
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

      <!-- DataTable表示 -->
      <div v-else>
        <DataTable 
          :value="raceDays" 
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
          <Column field="date" header="開催日" :sortable="true">
            <template #body="slotProps">
              <div class="font-semibold">{{ slotProps.data.date }}</div>
              <div class="text-sm text-surface-600">{{ slotProps.data.venue }}</div>
            </template>
          </Column>
          <Column field="races.length" header="レース数" :sortable="true">
            <template #body="slotProps">
              <Chip :label="`${slotProps.data.races.length}レース`" severity="info" size="small" />
            </template>
          </Column>
          <Column field="venue" header="競馬場" :sortable="true">
            <template #body="slotProps">
              <span class="font-medium">{{ slotProps.data.venue }}</span>
            </template>
          </Column>
          <Column header="アクション" :exportable="false">
            <template #body="slotProps">
              <Button
                label="詳細"
                icon="pi pi-arrow-right"
                size="small"
                @click="selectDate(slotProps.data)"
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
import AppLayout from '@/layouts/AppLayout.vue'
import { mockRaceMonths } from '@/utils/mockData'
import type { RaceDay } from '@/utils/mockData'
import { RouteName } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const { navigateTo, navigateTo404, getParams } = useNavigation()

const raceDays = ref<RaceDay[]>([])
const monthName = ref('')
const viewMode = ref<'card' | 'list'>('card')


const selectDate = (day: RaceDay) => {
  // ルートパラメータから年と月を取得
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam) {
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
  
  // 日付を選択した時は、その日の日付専用ページに遷移
  const dayNumber = parseInt(day.id.split('-')[2]) // day.idから日付を取得
  navigateTo(RouteName.RACE_LIST_IN_DAY, { year, month, day: dayNumber })
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



onMounted(() => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam) {
        navigateTo404()
    return
  }
  
  const monthId = `${yearParam}-${monthParam}`
  const monthData = mockRaceMonths.find(m => m.id === monthId)
  
  if (monthData) {
    monthName.value = monthData.name
    raceDays.value = monthData.days
  } else {
    navigateTo(RouteName.RACE_LIST_IN_YEAR, { year: new Date().getFullYear() })
  }
})
</script>
