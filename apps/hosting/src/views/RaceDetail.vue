<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div v-if="raceDetail" class="mb-2">
      <h1 class="text-3xl font-bold text-gray-900">{{ raceDetail.raceNumber }}R {{ raceDetail.raceName }}</h1>
      <p class="text-gray-600 mt-1">
        {{ raceDetail.racecourse }} - {{ formatDate(raceDetail.date) }}
        <span v-if="raceDetail.round || raceDetail.day" class="ml-2">
          <span v-if="raceDetail.round">第{{ raceDetail.round }}回</span>
          <span v-if="raceDetail.day">{{ formatDay(raceDetail.day) }}日目</span>
        </span>
      </p>
      
      <!-- レース情報タグ -->
      <div class="flex flex-wrap gap-2 mt-3">
        <Chip v-if="raceDetail.round" :label="`第${raceDetail.round}回`" severity="info" />
        <Chip v-if="raceDetail.day" :label="`${formatDay(raceDetail.day)}日目`" severity="info" />
        <Chip :label="raceDetail.distance ? `${raceDetail.distance}m` : '距離未定'" severity="info" />
        <Chip :label="raceDetail.surface || 'コース未定'" severity="secondary" />
        <Chip :label="raceDetail.weather || '天候未定'" severity="success" />
        <Chip :label="raceDetail.trackCondition || '馬場未定'" severity="warning" />
        <Chip v-if="raceDetail.grade" :label="raceDetail.grade" :severity="getGradeSeverity(raceDetail.grade)" />
      </div>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="text-center">
        <ProgressSpinner />
        <p class="mt-4 text-gray-600">レース詳細を読み込み中...</p>
      </div>
    </div>

    <!-- エラー -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="bg-red-50 border border-red-200 rounded-lg p-3">
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
    <div v-else-if="raceDetail" class="max-w-7xl mx-auto px-2 sm:px-4">
      <!-- 予測結果 -->
      <Card v-if="racePredictions.length > 0" class="mb-4">
        <template #header>
          <div class="p-3">
            <h3 class="text-xl font-bold">予測結果</h3>
            <p class="text-gray-600">{{ racePredictions.length }}頭</p>
          </div>
        </template>
        <template #content>
          <div class="p-3">
            <DataTable
              :value="racePredictions"
              :paginator="false"
              :rows="20"
              class="p-datatable-sm"
            >
              <Column field="predicted_rank" header="予測順位" :sortable="true" style="width: 80px">
                <template #body="{ data }">
                  <Chip :label="data.predicted_rank" :severity="data.predicted_rank <= 3 ? 'success' : 'secondary'" />
                </template>
              </Column>
              <Column field="horse_number" header="馬番" :sortable="true" style="width: 60px">
                <template #body="{ data }">
                  <Chip :label="data.horse_number" severity="info" />
                </template>
              </Column>
              <Column field="horse_name" header="馬名" :sortable="true">
                <template #body="{ data }">
                  <div class="font-medium">{{ data.horse_name }}</div>
                </template>
              </Column>
              <Column field="jockey_name" header="騎手" :sortable="true">
                <template #body="{ data }">
                  <div class="font-medium">{{ data.jockey_name }}</div>
                </template>
              </Column>
              <Column field="trainer_name" header="調教師" :sortable="true">
                <template #body="{ data }">
                  <div class="font-medium">{{ data.trainer_name }}</div>
                </template>
              </Column>
              <Column field="predicted_score" header="予測スコア" :sortable="true" style="width: 100px">
                <template #body="{ data }">
                  <div class="text-center font-medium">{{ data.predicted_score.toFixed(2) }}</div>
                </template>
              </Column>
            </DataTable>
          </div>
        </template>
      </Card>
      
      <!-- レース結果 -->
      <Card>
            <template #header>
              <div class="p-3">
                <h3 class="text-xl font-bold">レース結果</h3>
                <p class="text-gray-600">{{ raceDetail.results?.length || 0 }}頭</p>
              </div>
            </template>
            <template #content>
              <div class="p-3">
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
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNavigation } from '@/composables/useNavigation'
import { doc, getDoc, Timestamp } from 'firebase/firestore'
import { db } from '@/config/firebase'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { usePrediction } from '@/composables/usePrediction'
import { generateRaceKey } from '@/utils/raceKeyGenerator'

const router = useRouter()
const { getParam } = useNavigation()
const { getPredictionsByDate, getPredictionsByRaceKey } = usePrediction()

const navigateToRaceList = () => {
  router.push('/race-list')
}

const raceDetail = ref<Race | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const predictionsLoading = ref(false)
const predictionsData = ref<any>(null)

// レースキーを生成（raceDetailから）
const raceKey = computed(() => {
  if (!raceDetail.value) return null
  
  // 日付をDate型に変換
  const date = raceDetail.value.date instanceof Timestamp 
    ? raceDetail.value.date.toDate() 
    : raceDetail.value.date instanceof Date
    ? raceDetail.value.date
    : new Date(raceDetail.value.date)
  
  return generateRaceKey({
    date,
    racecourse: raceDetail.value.racecourse,
    raceNumber: raceDetail.value.raceNumber,
    round: raceDetail.value.round,
    day: raceDetail.value.day
  })
})

// 予測結果を取得
const racePredictions = computed(() => {
  if (!raceKey.value || !predictionsData.value) return []
  return getPredictionsByRaceKey(raceKey.value)
})

// 予測結果を読み込む
const loadPredictions = async () => {
  if (!raceDetail.value) return
  
  predictionsLoading.value = true
  try {
    const date = raceDetail.value.date instanceof Timestamp 
      ? raceDetail.value.date.toDate() 
      : raceDetail.value.date
    const dateStr = date.toISOString().split('T')[0]
    predictionsData.value = await getPredictionsByDate(dateStr)
  } catch (err: any) {
    console.error('予測結果の取得エラー:', err)
  } finally {
    predictionsLoading.value = false
  }
}

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

// 日目フォーマット関数（1, 2, 3, ..., a, b, cなど）
const formatDay = (day: string | number | null | undefined): string => {
  if (!day) return ''
  if (typeof day === 'number') return day.toString()
  return day.toString()
}


const getGradeSeverity = (grade: string | undefined) => {
  if (!grade) return 'contrast'
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



const fetchRaceDetail = async (raceKey: string) => {
  loading.value = true
  error.value = null
  
  try {
    // race_keyをドキュメントIDとして使用
    const raceDoc = await getDoc(doc(db, 'races', raceKey))
    
    if (raceDoc.exists()) {
      const data = raceDoc.data()
      raceDetail.value = {
        id: raceDoc.id,
        race_key: raceDoc.id, // ドキュメントIDがrace_key
        ...data
      } as Race
      
      // レース詳細取得後、予測結果を読み込む
      await loadPredictions()
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
  const raceKey = getParam('raceId') // パラメータ名はraceIdだが、値はrace_key
  if (raceKey) {
    fetchRaceDetail(raceKey)
  } else {
    navigateToRaceList()
  }
})
</script>
