<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div v-if="raceDetail" class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ raceDetail.raceNumber }}R {{ raceDetail.raceName }}</h1>
      <p class="text-gray-600 mt-1">{{ raceDetail.racecourse }} - {{ formatDate(raceDetail.date) }}</p>
      
      <!-- レース情報タグ -->
      <div class="flex flex-wrap gap-2 mt-3">
        <Chip :label="`${raceDetail.distance}m`" severity="info" />
        <Chip :label="raceDetail.surface" severity="secondary" />
        <Chip :label="raceDetail.weather" severity="success" />
        <Chip :label="raceDetail.trackCondition" severity="warning" />
        <Chip v-if="raceDetail.grade" :label="raceDetail.grade" :severity="getGradeSeverity(raceDetail.grade)" />
      </div>
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
            label="レース一覧に戻る"
            icon="pi pi-arrow-left"
            @click="navigateToRaceList"
          />
        </div>
      </div>
    </div>

    <!-- レース詳細 -->
    <div v-else-if="raceDetail" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- レース結果 -->
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
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import { doc, getDoc, Timestamp } from 'firebase/firestore'
import { db } from '@/config/firebase'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { RouteName } from '@/router/routeCalculator'

const { getParam, navigateTo } = useNavigation()

const navigateToRaceList = () => {
  navigateTo(RouteName.RACE_LIST_IN_YEAR, { year: new Date().getFullYear() })
}

const raceDetail = ref<Race | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// 日付フォーマット関数
const formatDate = (date: any) => {
  if (!date) return '日付不明'
  
  try {
    // Timestampの場合はtoDate()を使用、Dateの場合はそのまま使用
    const dateObj = date instanceof Timestamp ? date.toDate() : date
    return dateObj.toLocaleDateString('ja-JP')
  } catch (error) {
    console.error('日付フォーマットエラー:', error)
    return '日付エラー'
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
      navigateToRaceList()
    }
  } catch (err: any) {
    error.value = err.message
    console.error('レース詳細取得エラー:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const raceId = getParam('raceId')
  if (raceId) {
    fetchRaceDetail(raceId)
  } else {
    navigateToRaceList()
  }
})
</script>
