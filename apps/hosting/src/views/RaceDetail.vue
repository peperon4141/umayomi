<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div v-if="raceDetail" class="mb-2">
      <h1 class="text-3xl font-bold text-surface-900">{{ raceDetail.raceNumber }}R {{ raceDetail.raceName }}</h1>
      <p class="text-surface-600 mt-1">
        {{ raceDetail.racecourse }} - {{ raceDateLabel }}
        <span v-if="raceDetail.round" class="ml-2">
          <span v-if="raceDetail.round">第{{ raceDetail.round }}回</span>
        </span>
      </p>
      <div class="mt-2 flex flex-wrap gap-2">
        <Chip v-if="raceKey" :label="`race_key: ${raceKey}`" severity="secondary" class="font-mono text-xs" />
      </div>
      
      <!-- レース情報タグ -->
      <div class="flex flex-wrap gap-2 mt-3">
        <Chip v-if="raceDetail.round" :label="`第${raceDetail.round}回`" severity="info" />
        <Chip :label="raceDetail.distance ? `${raceDetail.distance}m` : '距離未定'" severity="info" />
        <Chip v-if="raceDetail.surface" :label="raceDetail.surface" severity="secondary" />
        <Tag v-else severity="warn" value="コース未定" />
        <Chip v-if="raceDetail.weather" :label="raceDetail.weather" severity="success" />
        <Tag v-else severity="warn" value="天候未定" />
        <Chip v-if="raceDetail.trackCondition" :label="raceDetail.trackCondition" severity="warning" />
        <Tag v-else severity="warn" value="馬場未定" />
        <Chip v-if="raceDetail.grade" :label="raceDetail.grade" :severity="getGradeSeverity(raceDetail.grade)" />
      </div>
      
      <!-- 予測実行ボタン -->
      <div class="mt-4">
        <Button
          label="予測実行"
          icon="pi pi-calculator"
          :loading="jrdbLoading"
          @click="runPrediction"
          :disabled="!raceDetail"
        />
        <Message v-if="jrdbError" severity="error" :closable="false" class="mt-2">
          {{ jrdbError }}
        </Message>
        <Message v-if="jrdbSuccess" severity="success" :closable="true" class="mt-2" @close="jrdbSuccess = null">
          {{ jrdbSuccess }}
        </Message>
      </div>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="text-center">
        <ProgressSpinner />
        <p class="mt-4 text-surface-600">レース詳細を読み込み中...</p>
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
      <Card class="mb-4">
        <template #header>
          <div class="p-3">
            <h3 class="text-xl font-bold">予測結果</h3>
            <p v-if="racePredictions.length > 0" class="text-gray-600">{{ racePredictions.length }}頭</p>
            <p v-else class="text-gray-500 text-sm">予測結果がありません（race_key: {{ raceKey }}）</p>
          </div>
        </template>
        <template #content>
          <div class="p-3">
            <div v-if="racePredictions.length === 0" class="text-center py-8 text-gray-500">
              <p>このレースに対する予測結果がありません。</p>
              <p class="text-sm mt-2">予測実行ボタンをクリックして予測を実行してください。</p>
            </div>
            <DataTable
              v-else
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNavigation } from '@/composables/useNavigation'
import { doc, getDoc, Timestamp } from 'firebase/firestore'
import { db } from '@/config/firebase'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { usePrediction } from '@/composables/usePrediction'
import { getFunctionUrl } from '@/utils/functionUrl'
import { getAuth } from 'firebase/auth'

const router = useRouter()
const { getParam } = useNavigation()
const { getPredictionsByDate, getPredictionsByRaceKey, watchPredictionsByDate, stopWatching } = usePrediction()

const navigateToRaceList = () => {
  router.push('/race-list')
}

const raceDetail = ref<Race | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const predictionsLoading = ref(false)
const jrdbLoading = ref(false)
const jrdbError = ref<string | null>(null)
const jrdbSuccess = ref<string | null>(null)

const requireRaceDate = (race: Race): Date => {
  const value = race.raceDate
  if (value) {
    const d = value instanceof Timestamp ? value.toDate() : value
    if (!(d instanceof Date) || isNaN(d.getTime())) throw new Error(`raceDate must be a valid Date/Timestamp (race_key=${race.race_key})`)
    return d
  }
  const legacyValue = (race as any).date
  if (!legacyValue) throw new Error(`raceDate is required (race_key=${race.race_key})`)
  const legacyDate = legacyValue instanceof Timestamp ? legacyValue.toDate() : legacyValue
  if (!(legacyDate instanceof Date) || isNaN(legacyDate.getTime())) throw new Error(`legacy date must be a valid Date/Timestamp (race_key=${race.race_key})`)
  return legacyDate
}

// 表示用（FirestoreのドキュメントIDと同一）
const raceKey = computed(() => (raceDetail.value ? raceDetail.value.race_key : null))
const raceDateLabel = computed(() => (raceDetail.value ? requireRaceDate(raceDetail.value).toLocaleDateString('ja-JP') : ''))

// 予測結果を取得（リアルタイムリスナーから直接取得）
const racePredictions = computed(() => {
  if (!raceKey.value) return []
  const filtered = getPredictionsByRaceKey(raceKey.value)
  return filtered
})

// 予測結果を読み込む（初回読み込み、リアルタイム監視開始前）
const loadPredictions = async () => {
  if (!raceDetail.value) return
  
  predictionsLoading.value = true
  try {
    const dateStr = requireRaceDate(raceDetail.value).toISOString().split('T')[0]
    await getPredictionsByDate(dateStr)
  } catch (err: any) {
    // 予測は一覧表示に必須ではないため、画面全体は落とさずにエラーを表示対象に回す
    jrdbError.value = err instanceof Error ? err.message : String(err)
  } finally {
    predictionsLoading.value = false
  }
}

// 予測結果をリアルタイムで監視
const startWatchingPredictions = () => {
  if (!raceDetail.value) return
  
  const dateStr = requireRaceDate(raceDetail.value).toISOString().split('T')[0]
  
  watchPredictionsByDate(dateStr)
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
    const yearStr = getParam('year')
    if (!yearStr) throw new Error('year param is required')
    // racesByYear/{year}/races/{race_id}
    const raceDoc = await getDoc(doc(db, 'racesByYear', yearStr, 'races', raceKey))
    
    if (raceDoc.exists()) {
      const data = raceDoc.data()
      raceDetail.value = {
        id: raceDoc.id,
        race_key: raceDoc.id, // ドキュメントIDがrace_key
        ...data
      } as Race
      
      // レース詳細取得後、予測結果をリアルタイムで監視開始
      await loadPredictions()
      startWatchingPredictions()
    } else {
      error.value = 'レースが見つかりません'
      navigateToRaceList()
    }
  } catch (err: any) {
    error.value = err instanceof Error ? err.message : String(err)
  } finally {
    loading.value = false
  }
}

const reloadRaceDetail = async () => {
  if (!raceKey.value) return
  const yearStr = getParam('year')
  if (!yearStr) throw new Error('year param is required')
  const raceDoc = await getDoc(doc(db, 'racesByYear', yearStr, 'races', raceKey.value))
  if (!raceDoc.exists()) return
  const data = raceDoc.data()
  raceDetail.value = {
    id: raceDoc.id,
    race_key: raceDoc.id,
    ...data
  } as Race
}

// 予測実行（JRDBデータ取得→結合→予測実行）
const runPrediction = async () => {
  if (!raceDetail.value) return
  
  jrdbLoading.value = true
  jrdbError.value = null
  jrdbSuccess.value = null
  
  try {
    // 日付を取得
    const dateStr = requireRaceDate(raceDetail.value).toISOString().split('T')[0]
    
    // 認証トークンを取得
    const auth = getAuth()
    const user = auth.currentUser
    if (!user) {
      throw new Error('ログインが必要です')
    }
    
    const token = await user.getIdToken()
    
    // Cloud Functionを呼び出し（JRDBデータ取得→結合→予測実行）
    const functionUrl = getFunctionUrl('runPredictionWithDataFetch')
    const url = new URL(functionUrl)
    url.searchParams.set('date', dateStr)
    // エミュレーター環境の判定
    const isEmulator = import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true' || import.meta.env.DEV
    url.searchParams.set('useEmulator', isEmulator ? 'true' : 'false')
    url.searchParams.set('autoSelectModel', 'true') // 最新のモデルを自動選択
    
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => null as any)
      const candidates: unknown[] = [
        errorData?.errorDetails,
        errorData?.stderr,
        errorData?.error
      ]
      const message = candidates.find((v) => typeof v === 'string' && (v as string).length > 0) as string | undefined
      if (message) throw new Error(message)
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      jrdbSuccess.value = `予測実行が完了しました。日付: ${result.date}、実行時間: ${Math.round(result.executionTimeMs / 1000)}秒`
      // 予測結果をリアルタイムで監視（既に監視中なら自動更新される）
      // 念のため、少し待ってから再読み込み
      setTimeout(async () => {
        await reloadRaceDetail()
        await loadPredictions()
      }, 2000) // 2秒待ってから再読み込み
    } else {
      const errorMessage = result?.error
      if (typeof errorMessage === 'string' && errorMessage.length > 0) throw new Error(errorMessage)
      throw new Error('予測実行に失敗しました')
    }
  } catch (err: any) {
    jrdbError.value = err instanceof Error ? err.message : String(err)
  } finally {
    jrdbLoading.value = false
  }
}

onMounted(() => {
  const raceKey = getParam('raceId') // パラメータ名はraceIdだが、値はrace_key
  const year = getParam('year')
  if (!raceKey || !year) return navigateToRaceList()
  fetchRaceDetail(raceKey)
})

// コンポーネントがアンマウントされたときに監視を停止
onUnmounted(() => {
  stopWatching()
})
</script>
