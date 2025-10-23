<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">競馬レース一覧</h1>
      <p class="text-gray-600 mt-1">開催月を選択してください</p>
    </div>

    <!-- 月一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import { mockRaceMonths } from '@/utils/mockData'
import type { RaceMonth } from '@/utils/mockData'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'

const router = useRouter()

const raceMonths = ref<RaceMonth[]>([])

const getTotalRaces = (month: RaceMonth) => {
  return month.days.reduce((total, day) => total + day.races.length, 0)
}

const selectMonth = (month: RaceMonth) => {
  // 月IDから年と月を抽出（例: "2024-10" -> year: 2024, month: 10）
  const [year, monthNum] = month.id.split('-')
  router.push(`/races/year/${year}/month/${monthNum}`)
}


onMounted(() => {
  raceMonths.value = mockRaceMonths
})
</script>
