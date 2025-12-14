<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-4">
      <h1 class="text-2xl sm:text-3xl font-bold text-surface-900">レースリスト</h1>
      <p class="text-sm sm:text-base text-surface-600 mt-1">全レース一覧</p>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="text-center">
        <i class="pi pi-spin pi-spinner text-4xl text-surface-500 mb-4"></i>
        <p class="text-surface-600">レースデータを読み込み中...</p>
      </div>
    </div>

    <!-- エラー -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <Message severity="error" :closable="false">{{ error }}</Message>
    </div>

    <!-- データなし -->
    <div v-else-if="raceDateItems.length === 0" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-surface-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-surface-900 mb-2">レースデータがありません</h3>
        <p class="text-surface-600">レースデータが見つかりませんでした。</p>
      </div>
    </div>

    <!-- レースリスト（DataTable） -->
    <div v-else class="max-w-7xl mx-auto px-2 sm:px-4">
      <Card>
        <template #content>
          <DataTable
            :value="raceDateItems"
            :scrollable="true"
            scrollHeight="600px"
            class="p-datatable-sm"
            :row-class="getRowClass"
            @row-click="onRowClick"
            :paginator="true"
            :rows="50"
            :rowsPerPageOptions="[10, 25, 50, 100]"
          >
            <Column field="displayDate" header="日付" :sortable="true">
              <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <span :class="{ 'font-bold': data.isCurrentMonth }">{{ data.displayDate }}</span>
                  <Chip v-if="data.isToday" label="今日" size="small" severity="info" />
                </div>
              </template>
            </Column>
            <Column field="raceCount" header="レース数" :sortable="true" style="width: 120px">
              <template #body="{ data }">
                <Chip :label="`${data.raceCount}レース`" size="small" severity="secondary" />
              </template>
            </Column>
            <Column field="year" header="年" :sortable="true" style="width: 80px" />
            <Column field="month" header="月" :sortable="true" style="width: 60px" />
            <Column field="day" header="日" :sortable="true" style="width: 60px" />
          </DataTable>
        </template>
      </Card>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { Timestamp } from 'firebase/firestore'
import { useRace } from '@/composables/useRace'
import { useNavigation } from '@/composables/useNavigation'
import { RouteName } from '@/router/routeCalculator'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'

interface RaceDateItem {
  dateKey: string  // "20251130" (YYYYMMDD)
  year: number
  month: number
  day: number
  raceCount: number
  isToday: boolean
  isCurrentMonth: boolean
  displayDate: string  // "2025年11月30日" (表示用)
}

const { races, fetchRaces } = useRace()
const { navigateTo } = useNavigation()

const loading = ref(false)
const error = ref<string | null>(null)
const raceDateItems = ref<RaceDateItem[]>([])

// 日付をYYYYMMDD形式に変換
const formatDateKey = (date: Date | Timestamp): string => {
  const d = date instanceof Timestamp ? date.toDate() : date
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}${month}${day}`
}

// YYYYMMDD形式から年月日を抽出
const parseDateKey = (dateKey: string): { year: number, month: number, day: number } => {
  if (dateKey.length !== 8) {
    throw new Error(`Invalid dateKey format: ${dateKey}. Expected YYYYMMDD format.`)
  }
  const year = parseInt(dateKey.substring(0, 4))
  const month = parseInt(dateKey.substring(4, 6))
  const day = parseInt(dateKey.substring(6, 8))
  return { year, month, day }
}

// 表示用の日付文字列を生成
const formatDisplayDate = (year: number, month: number, day: number): string => {
  return `${year}年${month}月${day}日`
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

// レースデータを日付でグループ化
const processRaceData = () => {
  const dateMap = new Map<string, Race[]>()

  races.value.forEach(race => {
    const date = race.date instanceof Timestamp ? race.date.toDate() : race.date
    const dateKey = formatDateKey(date)

    if (!dateMap.has(dateKey)) {
      dateMap.set(dateKey, [])
    }
    dateMap.get(dateKey)!.push(race)
  })

  const items: RaceDateItem[] = []
  const todayKey = formatDateKey(new Date())

  dateMap.forEach((raceList, dateKey) => {
    const { year, month, day } = parseDateKey(dateKey)
    const isToday = dateKey === todayKey
    const isCurrentMonth = year === today.value.year && month === today.value.month

    items.push({
      dateKey,
      year,
      month,
      day,
      raceCount: raceList.length,
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

  raceDateItems.value = items
}

// 行のクラスを取得（本日の月をハイライト）
const getRowClass = (data: RaceDateItem) => {
  if (data.isCurrentMonth) {
    return 'bg-primary-50'
  }
  return ''
}

// 行クリック時の処理
const onRowClick = (event: any) => {
  const item = event.data as RaceDateItem
  navigateTo(RouteName.RACE_LIST_IN_DAY, {
    year: item.year,
    month: item.month,
    day: item.day
  })
}

// データを読み込む
const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    if (races.value.length === 0) {
      const now = new Date()
      const startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
      const endDate = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())
      await fetchRaces(startDate, endDate)
    }
    processRaceData()
  } catch (err: any) {
    console.error('レースデータの取得エラー:', err)
    error.value = err.message || 'レースデータの取得に失敗しました'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

// レースデータが変更されたら再処理
watch(() => races.value, () => {
  processRaceData()
}, { deep: true })
</script>

<style scoped>
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

