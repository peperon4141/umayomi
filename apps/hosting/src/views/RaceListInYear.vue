<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">競馬レース一覧</h1>
      <p class="text-gray-600 mt-1">開催月を選択してください</p>
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

    <!-- 月一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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

      <!-- リスト表示 -->
      <div v-else class="space-y-4">
        <div
          v-for="month in raceMonths"
          :key="month.id"
          class="bg-surface-0 border border-surface-200 rounded-lg p-4 cursor-pointer hover:shadow-md transition-shadow duration-200"
          @click="selectMonth(month)"
        >
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-semibold text-surface-900">{{ month.name }}</h3>
              <p class="text-sm text-surface-600">開催日数: {{ month.days.length }}日</p>
            </div>
            <div class="flex items-center space-x-4">
              <Chip :label="`${month.days.length}日`" severity="info" />
              <Chip :label="`${getTotalRaces(month)}レース`" severity="success" />
              <Button
                label="詳細を見る"
                icon="pi pi-arrow-right"
                size="small"
                @click.stop="selectMonth(month)"
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
import type { RaceMonth } from '@/utils/mockData'
import { RouteName } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'

const { navigateTo, navigateTo404 } = useNavigation()

const raceMonths = ref<RaceMonth[]>([])
const viewMode = ref<'card' | 'list'>('card')

const getTotalRaces = (month: RaceMonth) => {
  return month.days.reduce((total, day) => total + day.races.length, 0)
}

const selectMonth = (month: RaceMonth) => {
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


onMounted(() => {
  raceMonths.value = mockRaceMonths
})
</script>
