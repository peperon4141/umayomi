<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ monthName }}</h1>
      <p class="text-gray-600 mt-1">開催日を選択してください</p>
    </div>

    <!-- 日付一覧 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="day in raceDays"
          :key="day.id"
          class="cursor-pointer hover:shadow-lg transition-shadow duration-200"
          @click="selectDate(day)"
        >
          <template #header>
            <div class="bg-blue-500 text-white p-4 text-center">
              <h3 class="text-lg font-bold">{{ day.date }}</h3>
              <p class="text-sm opacity-90">{{ day.venue }}</p>
            </div>
          </template>
          <template #content>
            <div class="p-4">
              <div class="flex justify-between items-center mb-4">
                <span class="text-sm text-gray-600">レース数</span>
                <Badge :value="`${day.races.length}レース`" severity="info" />
              </div>
              <div class="space-y-2">
                <div v-for="race in day.races.slice(0, 3)" :key="race.id" class="text-sm">
                  <div class="flex justify-between items-center">
                    <span class="font-medium">{{ race.raceNumber }}R</span>
                    <span class="text-gray-600">{{ race.startTime }}</span>
                  </div>
                  <div class="text-gray-700">{{ race.raceName }}</div>
                  <div class="text-xs text-gray-500">
                    {{ race.grade }} | {{ race.distance }}m | {{ race.surface }}
                  </div>
                </div>
                <div v-if="day.races.length > 3" class="text-gray-400 text-sm">
                  ...他{{ day.races.length - 3 }}レース
                </div>
              </div>
            </div>
          </template>
          <template #footer>
            <div class="p-4 bg-gray-50 text-center">
              <Button
                label="レース一覧を見る"
                icon="pi pi-arrow-right"
                class="w-full"
                @click="selectDate(day)"
              />
            </div>
          </template>
        </Card>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import { mockRaceMonths } from '@/utils/mockData'
import type { RaceDay } from '@/utils/mockData'

const router = useRouter()
const route = useRoute()

const raceDays = ref<RaceDay[]>([])
const monthName = ref('')


const selectDate = (day: RaceDay) => {
  router.push(`/races/date/${day.id}`)
}


onMounted(() => {
  const monthId = route.params.monthId as string
  const month = mockRaceMonths.find(m => m.id === monthId)
  
  if (month) {
    monthName.value = month.name
    raceDays.value = month.days
  } else {
    router.push('/races')
  }
})
</script>
