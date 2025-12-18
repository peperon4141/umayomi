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
            v-model:expandedRows="expandedRows"
            dataKey="dateKey"
            :scrollable="true"
            scrollHeight="600px"
            class="p-datatable-sm"
            :row-class="getRowClass"
            @row-click="onRowClick"
            :paginator="true"
            :rows="50"
            :rowsPerPageOptions="[10, 25, 50, 100]"
          >
            <Column :expander="true" style="width: 3rem" />
            <Column field="displayDate" header="日付" :sortable="true">
              <template #body="{ data }">
                <div class="flex items-center gap-2">
                  <span :class="{ 'font-bold': data.isCurrentMonth }">{{ data.displayDate }}</span>
                  <Chip v-if="data.isToday" label="今日" size="small" severity="info" />
                </div>
              </template>
            </Column>
            <Column header="JRA" style="width: 80px">
              <template #body="{ data }">
                <a
                  :href="getJRACalendarUrl(data.year, data.month, data.day)"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-primary-600 hover:text-primary-800 hover:underline"
                  @click.stop
                >
                  <i class="pi pi-external-link mr-1"></i>
                  詳細
                </a>
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
            <template #expansion="slotProps">
              <div class="p-4">
                <DataTable
                  :value="slotProps.data.races"
                  :paginator="false"
                  class="p-datatable-sm"
                >
                  <Column field="race_key" header="race_key" :sortable="false">
                    <template #body="{ data }">
                      <Chip :label="data.race_key" size="small" />
                    </template>
                  </Column>
                  <Column field="raceName" header="レース名" :sortable="false" />
                  <Column field="racecourse" header="競馬場" :sortable="false" style="width: 100px">
                    <template #body="{ data }">
                      <span v-if="data.racecourse">{{ data.racecourse }}</span>
                      <Tag v-else severity="danger" value="racecourse未設定" />
                    </template>
                  </Column>
                  <Column field="raceNumber" header="レース番号" :sortable="false" style="width: 100px" />
                  <Column field="raceStartTime" header="発走時刻" :sortable="false" style="width: 120px">
                    <template #body="{ data }">
                      <span v-if="data.raceStartTime">{{ formatTime(data.raceStartTime) }}</span>
                      <span v-else class="text-surface-400">-</span>
                    </template>
                  </Column>
                  <Column header="アクション" :exportable="false" style="width: 100px">
                    <template #body="{ data }">
                      <Button
                        label="詳細"
                        icon="pi pi-arrow-right"
                        size="small"
                        @click="selectRace(data)"
                      />
                    </template>
                  </Column>
                </DataTable>
              </div>
            </template>
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
  races: Race[]  // 該当日のレース一覧
}

const { races, fetchRaces } = useRace()
const { navigateTo } = useNavigation()

const loading = ref(false)
const error = ref<string | null>(null)
const raceDateItems = ref<RaceDateItem[]>([])
// dataKeyを使う場合、expandedRowsはオブジェクト形式（{ 'key': true }）が推奨
const expandedRows = ref<Record<string, boolean>>({})

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

// JRAカレンダーページのURLを生成
const getJRACalendarUrl = (year: number, month: number, day: number): string => {
  const monthStr = String(month).padStart(2, '0')
  const dayStr = String(day).padStart(2, '0')
  return `https://www.jra.go.jp/keiba/calendar${year}/${year}/${monthStr}/${monthStr}${dayStr}.html`
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
    let raceDateValue: unknown = race.raceDate
    if (!raceDateValue) {
      const legacyDate = (race as any).date
      if (!legacyDate) throw new Error(`raceDate is required but was missing (race.id=${race.id}, race_key=${race.race_key})`)
      raceDateValue = legacyDate
    }
    const raceDate = raceDateValue instanceof Timestamp 
      ? raceDateValue.toDate() 
      : raceDateValue
    if (!(raceDate instanceof Date)) throw new Error(`raceDate must be a Date or Timestamp (race.id=${race.id}, race_key=${race.race_key})`)
    const dateKey = formatDateKey(raceDate)

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
      displayDate: formatDisplayDate(year, month, day),
      races: raceList
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

// 時刻をフォーマット
const formatTime = (time: string | Date | Timestamp): string => {
  if (typeof time === 'string') return time
  if (time instanceof Timestamp) {
    const date = time.toDate()
    return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  }
  if (time instanceof Date) {
    return `${String(time.getHours()).padStart(2, '0')}:${String(time.getMinutes()).padStart(2, '0')}`
  }
  return '-'
}

// レース選択時の処理
const selectRace = (race: Race) => {
  if (!race.race_key) throw new Error(`race_key is required but was ${race.race_key}`)
  if (!race.year) throw new Error(`year is required but was ${race.year}`)
  navigateTo(RouteName.RACE_DETAIL_DIRECT, { year: race.year, raceId: race.race_key })
}

// 行クリック時の処理（展開/折りたたみを制御）
const onRowClick = (event: any) => {
  const target = event.originalEvent?.target as HTMLElement
  
  // 展開/折りたたみボタンがクリックされた場合は何もしない（DataTableが自動処理）
  if (target?.closest('.p-row-toggler')) return
  
  // リンクやボタンがクリックされた場合は何もしない
  if (target?.closest('a, button')) return
  
  // 行自体がクリックされた場合は展開/折りたたみを切り替え
  const rowData = event.data as RaceDateItem
  if (!rowData?.dateKey) return
  
  // 現在の展開状態を確認して切り替え
  const isExpanded = expandedRows.value[rowData.dateKey] === true
  expandedRows.value = {
    ...expandedRows.value,
    [rowData.dateKey]: !isExpanded
  }
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
    error.value = err instanceof Error ? err.message : 'レースデータの取得に失敗しました'
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

