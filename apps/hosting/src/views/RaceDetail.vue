<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ raceDetail?.raceNumber }}R {{ raceDetail?.raceName }}</h1>
      <p class="text-gray-600 mt-1">{{ raceDetail?.venue }} - {{ raceDetail?.startTime }}</p>
    </div>

    <!-- レース詳細 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- レース情報 -->
        <div class="lg:col-span-1">
          <Card>
            <template #header>
              <div class="p-4 text-center" :class="getGradeColor(raceDetail?.grade || '')">
                <h3 class="text-xl font-bold text-white">{{ raceDetail?.raceNumber }}R</h3>
                <p class="text-sm text-white opacity-90">{{ raceDetail?.startTime }}</p>
              </div>
            </template>
            <template #content>
              <div class="p-4 space-y-4">
                <div>
                  <h4 class="font-bold text-lg mb-2">{{ raceDetail?.raceName }}</h4>
                  <div class="flex flex-wrap gap-2 mb-3">
                    <Chip :label="raceDetail?.grade" :severity="getGradeSeverity(raceDetail?.grade || '')" />
                    <Chip :label="`${raceDetail?.distance}m`" severity="info" />
                    <Chip :label="raceDetail?.surface" severity="secondary" />
                  </div>
                </div>
                
                <div class="space-y-3">
                  <div class="flex justify-between">
                    <span class="text-gray-600">賞金</span>
                    <span class="font-medium">{{ formatPrize(raceDetail?.prize || 0) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">競馬場</span>
                    <span class="font-medium">{{ raceDetail?.venue }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">年齢</span>
                    <span class="font-medium">{{ raceDetail?.age }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">斤量</span>
                    <span class="font-medium">{{ raceDetail?.weight }}</span>
                  </div>
                </div>
                
                <div class="mt-4 p-3 bg-gray-50 rounded">
                  <p class="text-sm text-gray-700">{{ raceDetail?.description }}</p>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- 出走馬一覧 -->
        <div class="lg:col-span-2">
          <Card>
            <template #header>
              <div class="p-4">
                <h3 class="text-xl font-bold">出走馬一覧</h3>
                <p class="text-gray-600">{{ raceDetail?.horses.length }}頭</p>
              </div>
            </template>
            <template #content>
              <div class="p-4">
                <DataTable
                  :value="raceDetail?.horses"
                  :paginator="false"
                  :rows="20"
                  class="p-datatable-sm"
                >
                  <Column field="number" header="馬番" :sortable="true" style="width: 60px">
                    <template #body="{ data }">
                      <Chip :label="data.number" severity="info" />
                    </template>
                  </Column>
                  <Column field="name" header="馬名" :sortable="true">
                    <template #body="{ data }">
                      <div class="font-medium">{{ data.name }}</div>
                      <div class="text-xs text-gray-500">{{ data.color }} {{ data.sex }}</div>
                    </template>
                  </Column>
                  <Column field="jockey" header="騎手" :sortable="true">
                    <template #body="{ data }">
                      <div class="font-medium">{{ data.jockey }}</div>
                    </template>
                  </Column>
                  <Column field="trainer" header="調教師" :sortable="true">
                    <template #body="{ data }">
                      <div class="font-medium">{{ data.trainer }}</div>
                    </template>
                  </Column>
                  <Column field="weight" header="斤量" :sortable="true" style="width: 80px">
                    <template #body="{ data }">
                      <div class="text-center">{{ data.weight }}kg</div>
                    </template>
                  </Column>
                  <Column field="odds" header="オッズ" :sortable="true" style="width: 80px">
                    <template #body="{ data }">
                      <div class="text-center font-medium">{{ data.odds }}</div>
                    </template>
                  </Column>
                </DataTable>
              </div>
            </template>
          </Card>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import { mockRaceDetails, mockRaceMonths } from '@/utils/mockData'
import type { RaceDetail } from '@/utils/mockData'

const router = useRouter()
const route = useRoute()

const raceDetail = ref<RaceDetail | null>(null)
const monthName = ref('')
const raceName = ref('')


const getGradeColor = (grade: string) => {
  switch (grade) {
    case 'GⅠ':
      return 'bg-red-600'
    case 'GⅡ':
      return 'bg-orange-500'
    case 'GⅢ':
      return 'bg-yellow-500'
    case 'オープン':
      return 'bg-purple-500'
    case '3勝クラス':
      return 'bg-blue-500'
    case '2勝クラス':
      return 'bg-green-500'
    case '1勝クラス':
      return 'bg-teal-500'
    case '新馬':
      return 'bg-indigo-500'
    case '未勝利':
      return 'bg-gray-500'
    default:
      return 'bg-gray-500'
  }
}

const getGradeSeverity = (grade: string) => {
  switch (grade) {
    case 'GⅠ':
      return 'danger'
    case 'GⅡ':
      return 'warning'
    case 'GⅢ':
      return 'info'
    case 'オープン':
      return 'secondary'
    case '3勝クラス':
      return 'info'
    case '2勝クラス':
      return 'success'
    case '1勝クラス':
      return 'info'
    case '新馬':
      return 'secondary'
    case '未勝利':
      return 'contrast'
    default:
      return 'contrast'
  }
}

const formatPrize = (prize: number) => {
  if (prize >= 1000000) {
    return `${(prize / 1000000).toFixed(0)}万円`
  } else if (prize >= 1000) {
    return `${(prize / 1000).toFixed(0)}千円`
  } else {
    return `${prize}円`
  }
}


onMounted(() => {
  const raceId = route.params.raceId as string
  
  // レース詳細を取得
  raceDetail.value = mockRaceDetails[raceId] || null
  
  if (raceDetail.value) {
    raceName.value = `${raceDetail.value.raceNumber}R ${raceDetail.value.raceName}`
    
    // 月名を取得するために全月を検索
    for (const month of mockRaceMonths) {
      for (const day of month.days) {
        const race = day.races.find(r => r.id === raceId)
        if (race) {
          monthName.value = month.name
          break
        }
      }
      if (monthName.value) break
    }
  } else {
    router.push('/races/year/2024')
  }
})
</script>
