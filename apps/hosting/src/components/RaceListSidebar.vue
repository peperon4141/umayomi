<template>
  <div class="race-list-sidebar">
    <DataTable
      :value="raceDateItems"
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
import { Timestamp } from 'firebase/firestore'
import { useRace } from '@/composables/useRace'
// navigateは現状未使用（サイドバーは一覧表示のみ）
import type { Race } from '../../../shared/race'

interface RaceDateItem {
  dateKey: string  // "20251130" (race_keyの拡張形式の日付部分、YYYYMMDD)
  year: number
  month: number
  day: number
  raceCount: number
  isToday: boolean
  isCurrentMonth: boolean
  displayDate: string  // "2025年11月30日" (表示用)
}

const { races, fetchRaces } = useRace()
const raceDateItems = ref<RaceDateItem[]>([])

// 日付をYYYYMMDD形式に変換（race_keyの拡張形式の日付部分と同じ形式）
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
    const raceDateValue = race.raceDate || (race as any).date
    const raceDate = raceDateValue instanceof Timestamp 
      ? raceDateValue.toDate() 
      : raceDateValue
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

// 行クリック時の処理（日付詳細ページは削除されたため、何もしない）
const onRowClick = () => {
  // 日付詳細ページは削除されたため、クリック時は何もしない
  // 必要に応じて、レースリストページに遷移するなどの処理を追加可能
}

// データを読み込む
const loadData = async () => {
  if (races.value.length === 0) {
    const now = new Date()
    const startDate = new Date(now.getFullYear() - 1, now.getMonth(), now.getDate())
    const endDate = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate())
    await fetchRaces(startDate, endDate)
  }
  processRaceData()
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
.race-list-sidebar {
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

