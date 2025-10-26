<template>
  <div class="space-y-6">
    <!-- ページヘッダー -->
    <div class="mb-8">
      <h2 class="text-3xl font-bold text-surface-900 mb-2">スクレイピング管理</h2>
      <p class="text-surface-600">Cloud Functionsを実行し、スクレイピング履歴を管理</p>
    </div>

    <!-- スクレイピング統計 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card class="bg-blue-600 text-white">
        <template #content>
          <div class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-white text-sm font-medium opacity-80">総実行回数</p>
                <p class="text-3xl font-bold">{{ totalExecutions }}</p>
              </div>
              <i class="pi pi-play text-4xl text-white opacity-60"></i>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-green-600 text-white">
        <template #content>
          <div class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-white text-sm font-medium opacity-80">成功回数</p>
                <p class="text-3xl font-bold">{{ successCount }}</p>
              </div>
              <i class="pi pi-check text-4xl text-white opacity-60"></i>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-red-600 text-white">
        <template #content>
          <div class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-white text-sm font-medium opacity-80">失敗回数</p>
                <p class="text-3xl font-bold">{{ failureCount }}</p>
              </div>
              <i class="pi pi-times text-4xl text-white opacity-60"></i>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-purple-600 text-white">
        <template #content>
          <div class="p-6">
            <div class="flex items-center justify-between">
              <div>
                <p class="text-white text-sm font-medium opacity-80">成功率</p>
                <p class="text-3xl font-bold">{{ successRate }}%</p>
              </div>
              <i class="pi pi-percentage text-4xl text-white opacity-60"></i>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- タスク選択 -->
    <div class="mb-8">
      <Card>
        <template #header>
          <div class="p-6 border-b border-surface-border">
            <h3 class="text-xl font-bold text-surface-900">実行タスク選択</h3>
            <p class="text-surface-600 mt-1">実行するスクレイピングタスクを選択してください</p>
          </div>
        </template>
        <template #content>
          <div class="p-6">
            <div class="mb-4">
              <label class="block text-sm font-medium text-surface-900 mb-2">タスク</label>
              <Dropdown
                v-model="selectedTask"
                :options="taskOptions"
                option-label="label"
                option-value="value"
                placeholder="タスクを選択してください"
                class="w-full"
              />
            </div>
            
            <!-- 選択されたタスクに応じた入力フィールド -->
            <div v-if="selectedTask" class="space-y-4">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label class="block text-sm font-medium text-surface-900 mb-2">年</label>
                  <InputNumber
                    v-model="year"
                    :min="2020"
                    :max="2030"
                    placeholder="年"
                    class="w-full"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-surface-900 mb-2">月</label>
                  <Dropdown
                    v-model="month"
                    :options="monthOptions"
                    option-label="label"
                    option-value="value"
                    placeholder="月"
                    class="w-full"
                  />
                </div>
                <div v-if="selectedTask === 'raceResult'">
                  <label class="block text-sm font-medium text-surface-900 mb-2">日</label>
                  <InputNumber
                    v-model="day"
                    :min="1"
                    :max="31"
                    placeholder="日"
                    class="w-full"
                  />
                </div>
              </div>
              
              <div class="flex justify-end">
                <Button
                  :label="getTaskButtonLabel()"
                  :icon="getTaskIcon()"
                  :severity="getTaskSeverity()"
                  @click="executeTask"
                  :disabled="!isFormValid"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Functions Log -->
    <div class="mb-8">
      <Card>
        <template #header>
          <div class="p-6 border-b border-surface-border">
            <div class="flex justify-between items-center">
              <div>
                <h3 class="text-xl font-bold text-surface-900">Functions Log</h3>
                <p class="text-surface-600 mt-1">スクレイピング処理の実行履歴</p>
              </div>
              <Button
                icon="pi pi-refresh"
                severity="secondary"
                text
                @click="refreshData"
                v-tooltip.top="'ログを更新'"
              />
            </div>
          </div>
        </template>
        <template #content>
          <div class="p-6">
            <!-- ローディング -->
            <div v-if="functionLogLoading" class="text-center py-8">
              <ProgressSpinner />
              <p class="mt-4 text-surface-600">ログを読み込み中...</p>
            </div>

            <!-- エラー -->
            <div v-else-if="functionLogError" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
              <i class="pi pi-exclamation-triangle text-red-500 text-4xl mb-4"></i>
              <h3 class="text-red-800 font-medium mb-2">エラーが発生しました</h3>
              <p class="text-red-600">{{ functionLogError }}</p>
            </div>

            <!-- ログ一覧 -->
            <div v-else-if="functionLogs.length > 0" class="space-y-4">
              <div v-for="log in functionLogs" :key="log.id" 
                   :class="log.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
                   class="border rounded-lg p-4">
                <div class="flex justify-between items-start mb-2">
                  <div class="flex items-center gap-2">
                    <Chip 
                      :label="log.functionName" 
                      :severity="log.success ? 'success' : 'danger'"
                      size="small" 
                    />
                    <Chip 
                      :label="`${log.year}年${log.month}月`" 
                      severity="info"
                      size="small" 
                    />
                    <Chip 
                      v-if="log.executionTimeMs"
                      :label="`${log.executionTimeMs}ms`" 
                      severity="secondary"
                      size="small" 
                    />
                  </div>
                  <div class="text-sm text-surface-500">
                    {{ formatLogDate(log.timestamp) }}
                  </div>
                </div>
                
                <p class="text-sm font-medium mb-2">{{ log.message }}</p>
                
                <div v-if="log.success && log.additionalData" class="text-sm text-surface-600 space-y-1">
                  <div v-for="(value, key) in log.additionalData" :key="key">
                    {{ formatAdditionalDataKey(key) }}: {{ formatAdditionalDataValue(value) }}
                  </div>
                </div>
                
                <div v-else-if="log.error" class="text-sm text-red-600">
                  エラー: {{ log.error }}
                </div>
              </div>
            </div>

            <!-- データなし -->
            <div v-else class="text-center py-8">
              <i class="pi pi-list text-6xl text-surface-400 mb-4"></i>
              <h3 class="text-xl font-semibold text-surface-900 mb-2">ログがありません</h3>
              <p class="text-surface-600">スクレイピング処理を実行すると、ここにログが表示されます。</p>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFunctionLog } from '@/composables/useFunctionLog'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import ProgressSpinner from 'primevue/progressspinner'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'

const { logs: functionLogs, loading: functionLogLoading, error: functionLogError, fetchFunctionLogs } = useFunctionLog()

// タスク選択関連
const selectedTask = ref<string | null>(null)
const year = ref<number | null>(new Date().getFullYear())
const month = ref<number | null>(new Date().getMonth() + 1)
const day = ref<number | null>(new Date().getDate())

// タスクオプション
const taskOptions = ref([
  { label: 'カレンダーデータ取得', value: 'calendar' },
  { label: 'レース結果データ取得', value: 'raceResult' },
  { label: '一括データ取得', value: 'batch' }
])

// 月オプション
const monthOptions = ref([
  { label: '1月', value: 1 },
  { label: '2月', value: 2 },
  { label: '3月', value: 3 },
  { label: '4月', value: 4 },
  { label: '5月', value: 5 },
  { label: '6月', value: 6 },
  { label: '7月', value: 7 },
  { label: '8月', value: 8 },
  { label: '9月', value: 9 },
  { label: '10月', value: 10 },
  { label: '11月', value: 11 },
  { label: '12月', value: 12 }
])

// フォームバリデーション
const isFormValid = computed(() => {
  if (!selectedTask.value || !year.value || !month.value) return false
  if (selectedTask.value === 'raceResult' && !day.value) return false
  return true
})

// タスクボタンのラベル
const getTaskButtonLabel = () => {
  const task = taskOptions.value.find(t => t.value === selectedTask.value)
  return task?.label || '実行'
}

// タスクボタンのアイコン
const getTaskIcon = () => {
  switch (selectedTask.value) {
    case 'calendar': return 'pi pi-calendar'
    case 'raceResult': return 'pi pi-trophy'
    case 'batch': return 'pi pi-download'
    default: return 'pi pi-play'
  }
}

// タスクボタンの色
const getTaskSeverity = () => {
  switch (selectedTask.value) {
    case 'calendar': return 'primary'
    case 'raceResult': return 'success'
    case 'batch': return 'info'
    default: return 'primary'
  }
}

// タスク実行
const executeTask = async () => {
  if (!isFormValid.value) return
  
  console.log('タスク実行:', {
    task: selectedTask.value,
    year: year.value,
    month: month.value,
    day: day.value
  })
  
  // TODO: 実際のCloud Functions呼び出しを実装
  await refreshData()
}

// 統計データの計算
const totalExecutions = computed(() => functionLogs.value.length)
const successCount = computed(() => functionLogs.value.filter(log => log.success).length)
const failureCount = computed(() => functionLogs.value.filter(log => !log.success).length)
const successRate = computed(() => {
  if (totalExecutions.value === 0) return 0
  return Math.round((successCount.value / totalExecutions.value) * 100)
})

// ログ日付フォーマット関数
const formatLogDate = (date: Date) => {
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// additionalDataのキーを日本語に変換
const formatAdditionalDataKey = (key: string) => {
  const keyMap: Record<string, string> = {
    racesCount: 'レース数',
    savedCount: '保存数',
    calendarRacesCount: 'カレンダーレース',
    raceResultsCount: 'レース結果',
    totalRacesCount: '総レース数',
    processedDates: '処理日数',
    url: 'URL',
    calendarUrl: 'カレンダーURL',
    executionTimeMs: '実行時間'
  }
  return keyMap[key] || key
}

// additionalDataの値をフォーマット
const formatAdditionalDataValue = (value: any) => {
  if (Array.isArray(value)) {
    return `${value.length}件`
  }
  if (typeof value === 'number') {
    if (value > 1000) {
      return `${value}ms`
    }
    return `${value}件`
  }
  if (typeof value === 'string') {
    return value
  }
  return String(value)
}

const refreshData = async () => {
  await fetchFunctionLogs()
}

onMounted(async () => {
  await fetchFunctionLogs()
})
</script>
