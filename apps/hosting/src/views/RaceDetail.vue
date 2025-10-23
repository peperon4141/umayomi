<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div v-if="raceDetail" class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ raceDetail.raceNumber }}R {{ raceDetail.raceName }}</h1>
      <p class="text-gray-600 mt-1">{{ raceDetail.racecourse }} - {{ new Date(raceDetail.date).toLocaleDateString('ja-JP') }}</p>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <ProgressSpinner />
        <p class="mt-4 text-gray-600">レース詳細を読み込み中...</p>
      </div>
    </div>

    <!-- エラー -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6">
        <div class="flex items-center">
          <i class="pi pi-exclamation-triangle text-red-500 text-xl mr-3"></i>
          <div>
            <h3 class="text-red-800 font-medium">エラーが発生しました</h3>
            <p class="text-red-600 mt-1">{{ error }}</p>
          </div>
        </div>
        <div class="mt-4">
          <Button
            label="ダッシュボードに戻る"
            icon="pi pi-arrow-left"
            @click="router.push('/dashboard')"
          />
        </div>
      </div>
    </div>

    <!-- レース詳細 -->
    <div v-else-if="raceDetail" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- レース情報 -->
        <div class="lg:col-span-1">
          <Card>
            <template #header>
              <div class="p-4 text-center" :class="getGradeColor(raceDetail.grade || '')">
                <h3 class="text-xl font-bold text-white">{{ raceDetail.raceNumber }}R</h3>
                <p class="text-sm text-white opacity-90">{{ raceDetail.raceName }}</p>
              </div>
            </template>
            <template #content>
              <div class="p-4 space-y-4">
                <div>
                  <div class="flex flex-wrap gap-2 mb-3">
                    <Chip :label="raceDetail.grade" :severity="getGradeSeverity(raceDetail.grade || '')" />
                    <Chip :label="`${raceDetail.distance}m`" severity="info" />
                    <Chip :label="raceDetail.surface" severity="secondary" />
                  </div>
                </div>
                
                <div class="space-y-3">
                  <div class="flex justify-between">
                    <span class="text-gray-600">競馬場</span>
                    <span class="font-medium">{{ raceDetail.racecourse }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">天気</span>
                    <span class="font-medium">{{ raceDetail.weather }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">馬場状態</span>
                    <span class="font-medium">{{ raceDetail.trackCondition }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-gray-600">開催日</span>
                    <span class="font-medium">{{ new Date(raceDetail.date).toLocaleDateString('ja-JP') }}</span>
                  </div>
                </div>
              </div>
            </template>
          </Card>
        </div>

        <!-- レース結果 -->
        <div class="lg:col-span-2">
          <Card>
            <template #header>
              <div class="p-4">
                <h3 class="text-xl font-bold">レース結果</h3>
                <p class="text-gray-600">{{ raceDetail.results?.length || 0 }}頭</p>
              </div>
            </template>
            <template #content>
              <div class="p-4">
                <DataTable
                  :value="raceDetail.results || []"
                  :paginator="false"
                  :rows="20"
                  class="p-datatable-sm"
                >
                  <Column field="rank" header="着順" :sortable="true" style="width: 60px">
                    <template #body="{ data }">
                      <Chip :label="data.rank" :severity="data.rank <= 3 ? 'success' : 'secondary'" />
                    </template>
                  </Column>
                  <Column field="horseNumber" header="馬番" :sortable="true" style="width: 60px">
                    <template #body="{ data }">
                      <Chip :label="data.horseNumber" severity="info" />
                    </template>
                  </Column>
                  <Column field="horseName" header="馬名" :sortable="true">
                    <template #body="{ data }">
                      <div class="font-medium">{{ data.horseName }}</div>
                    </template>
                  </Column>
                  <Column field="jockey" header="騎手" :sortable="true">
                    <template #body="{ data }">
                      <div class="font-medium">{{ data.jockey }}</div>
                    </template>
                  </Column>
                  <Column field="time" header="タイム" :sortable="true" style="width: 80px">
                    <template #body="{ data }">
                      <div class="text-center font-medium">{{ data.time }}</div>
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
import { doc, getDoc } from 'firebase/firestore'
import { db } from '@/config/firebase'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '@/types/race'

const router = useRouter()
const route = useRoute()

const raceDetail = ref<Race | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)


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


const fetchRaceDetail = async (raceId: string) => {
  loading.value = true
  error.value = null
  
  try {
    const raceDoc = await getDoc(doc(db, 'races', raceId))
    
    if (raceDoc.exists()) {
      raceDetail.value = {
        id: raceDoc.id,
        ...raceDoc.data()
      } as Race
    } else {
      error.value = 'レースが見つかりません'
      router.push('/dashboard')
    }
  } catch (err: any) {
    error.value = err.message
    console.error('レース詳細取得エラー:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const raceId = route.params.raceId as string
  if (raceId) {
    fetchRaceDetail(raceId)
  } else {
    router.push('/dashboard')
  }
})
</script>
