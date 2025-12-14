<template>
  <div class="prediction-list-sidebar">
    <div v-if="loading" class="text-center py-2">
      <i class="pi pi-spin pi-spinner text-surface-500"></i>
    </div>
    <div v-else-if="error || localError" class="text-sm text-red-600 px-2 py-1">
      {{ error || localError }}
    </div>
    <div v-else-if="predictionDateItems.length === 0" class="text-sm text-surface-500 px-2 py-1">
      予測結果がありません
    </div>
    <DataTable
      v-else
      :value="predictionDateItems"
      :scrollable="true"
      scrollHeight="calc(100vh - 20rem)"
      class="p-datatable-sm"
      :row-class="getRowClass"
      @row-click="onRowClick"
    >
      <Column field="displayDate" header="日付" :sortable="true">
        <template #body="{ data }">
          <div class="flex items-center gap-2">
            <span :class="{ 'font-bold': data.isCurrentMonth }">{{ data.displayDate }}</span>
            <Chip v-if="data.isToday" label="今日" size="small" severity="info" />
          </div>
        </template>
      </Column>
      <Column field="raceCount" header="レース数" :sortable="true" style="width: 80px">
        <template #body="{ data }">
          <Chip :label="`${data.raceCount}レース`" size="small" severity="secondary" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { usePrediction, type PredictionDocument } from '@/composables/usePrediction'
import { useNavigation } from '@/composables/useNavigation'
import { RouteName } from '@/router/routeCalculator'

interface PredictionDateItem {
  dateKey: string  // "2025-11-30" (YYYY-MM-DD)
  year: number
  month: number
  day: number
  raceCount: number
  isToday: boolean
  isCurrentMonth: boolean
  displayDate: string  // "2025年11月30日" (表示用)
}

const { loading, error, getRecentPredictions } = usePrediction()
const { navigateTo } = useNavigation()

const predictionDocuments = ref<PredictionDocument[]>([])
const predictionDateItems = ref<PredictionDateItem[]>([])
const localError = ref<string | null>(null)

// 日付文字列（YYYY-MM-DD）から年月日を抽出
const parseDateString = (dateStr: string): { year: number, month: number, day: number } => {
  const [year, month, day] = dateStr.split('-').map(Number)
  return { year, month, day }
}

// 表示用の日付文字列を生成
const formatDisplayDate = (year: number, month: number, day: number): string => {
  return `${year}年${month}月${day}日`
}

// YYYY-MM-DD形式の日付文字列を生成
const formatDateKey = (year: number, month: number, day: number): string => {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

// 本日の日付を取得
const today = computed(() => {
  const now = new Date()
  return {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    day: now.getDate()
  }
})

// 予測結果データを日付でグループ化
const processPredictionData = () => {
  const dateMap = new Map<string, Set<string>>()
  
  predictionDocuments.value.forEach(doc => {
    const dateStr = doc.date
    const { year, month, day } = parseDateString(dateStr)
    
    // レースキーからユニークなレース数をカウント
    const raceKeys = new Set<string>()
    doc.predictions.forEach(pred => {
      raceKeys.add(pred.race_key)
    })
    
    const dateKey = formatDateKey(year, month, day)
    if (!dateMap.has(dateKey)) {
      dateMap.set(dateKey, new Set())
    }
    raceKeys.forEach(raceKey => dateMap.get(dateKey)!.add(raceKey))
  })
  
  const items: PredictionDateItem[] = []
  const todayKey = formatDateKey(today.value.year, today.value.month, today.value.day)
  
  dateMap.forEach((raceKeySet, dateKey) => {
    const { year, month, day } = parseDateString(dateKey)
    const isToday = dateKey === todayKey
    const isCurrentMonth = year === today.value.year && month === today.value.month
    
    items.push({
      dateKey,
      year,
      month,
      day,
      raceCount: raceKeySet.size,
      isToday,
      isCurrentMonth,
      displayDate: formatDisplayDate(year, month, day)
    })
  })
  
  // 日付でソート（新しい順）
  items.sort((a, b) => {
    if (a.dateKey > b.dateKey) return -1
    if (a.dateKey < b.dateKey) return 1
    return 0
  })
  
  predictionDateItems.value = items
}

// 行のクラスを取得（本日の月をハイライト）
const getRowClass = (data: PredictionDateItem) => {
  if (data.isCurrentMonth) {
    return 'bg-primary-50'
  }
  return ''
}

// 行クリック時の処理
const onRowClick = (event: any) => {
  const item = event.data as PredictionDateItem
  navigateTo(RouteName.RACE_LIST_IN_DAY, {
    year: item.year,
    month: item.month,
    day: item.day
  })
}

// データを読み込む
const loadData = async () => {
  localError.value = null
  try {
    const docs = await getRecentPredictions(30) // 最近30件の予測結果を取得
    console.log('予測結果取得:', docs.length, '件')
    predictionDocuments.value = docs
    processPredictionData()
    if (docs.length === 0) {
      console.log('予測結果が0件です')
    }
  } catch (err: any) {
    console.error('予測結果の取得エラー:', err)
    localError.value = err.message || '予測結果の取得に失敗しました'
  }
}

onMounted(() => {
  loadData()
})

// 予測結果データが変更されたら再処理
watch(() => predictionDocuments.value, () => {
  processPredictionData()
}, { deep: true })
</script>

<style scoped>
.prediction-list-sidebar {
  width: 100%;
}

:deep(.p-datatable-sm .p-datatable-tbody > tr) {
  cursor: pointer;
}

:deep(.p-datatable-sm .p-datatable-tbody > tr:hover) {
  background-color: var(--p-surface-100);
}

:deep(.p-datatable-sm .p-datatable-tbody > tr.bg-primary-50) {
  background-color: var(--p-primary-50);
}

:deep(.p-datatable-sm .p-datatable-tbody > tr.bg-primary-50:hover) {
  background-color: var(--p-primary-100);
}
</style>

