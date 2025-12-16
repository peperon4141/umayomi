<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-2">
      <div class="flex items-center gap-3">
        <h1 class="text-2xl sm:text-3xl font-bold text-surface-900">{{ dayName }}</h1>
        <a
          :href="getJRAUrlForDay()"
          target="_blank"
          rel="noopener noreferrer"
          class="text-primary hover:text-primary-600 transition-colors inline-flex items-center"
          v-tooltip.top="'JRA公式サイトでレース結果を見る'"
        >
          <i class="pi pi-external-link text-lg"></i>
        </a>
      </div>
      <p class="text-sm sm:text-base text-surface-600 mt-1">その日のレース一覧</p>
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
      <div class="bg-red-50 border border-red-200 rounded-lg p-3 text-center">
        <i class="pi pi-exclamation-triangle text-red-500 text-4xl mb-4"></i>
        <h3 class="text-red-800 font-medium mb-2">エラーが発生しました</h3>
        <p class="text-red-600">{{ error }}</p>
      </div>
    </div>

    <!-- データなし -->
    <div v-else-if="dayRaces.length === 0" class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-surface-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-surface-900 mb-2">レースデータがありません</h3>
        <p class="text-surface-600">指定された日のレースが見つかりませんでした。</p>
      </div>
    </div>

    <!-- レース一覧（競馬場ごとにグループ化、DataTable Expansion機能使用） -->
    <div v-else class="max-w-7xl mx-auto px-2 sm:px-4">
      <DataTable
        :value="venueGroups"
        v-model:expandedRows="expandedRows"
        dataKey="venue"
        class="p-datatable-sm"
      >
        <Column :expander="true" style="width: 3rem" />
        <Column field="venue" header="競馬場" :sortable="false">
          <template #body="{ data }">
            <div class="font-semibold text-lg">{{ data.venue }}</div>
          </template>
        </Column>
        <Column field="raceCount" header="レース数" :sortable="false" style="width: 100px">
          <template #body="{ data }">
            <Chip :label="`${data.raceCount}レース`" severity="info" />
          </template>
        </Column>
        <template #expansion="slotProps">
          <div class="p-4">
            <DataTable
              :value="slotProps.data.races"
              :paginator="false"
              class="p-datatable-sm"
            >
              <Column field="raceNumber" header="レース番号" :sortable="false" style="width: 80px">
                <template #body="{ data }">
                  <Chip :label="String(data.raceNumber)" severity="info" />
                </template>
              </Column>
              <Column field="raceName" header="レース名" :sortable="false">
                <template #body="{ data }">
                  <div class="font-semibold">{{ data.raceName }}</div>
                  <div class="text-sm text-surface-600 mt-1">
                    <span v-if="data.round">第{{ data.round }}回 </span>
                    <span v-if="data.grade">{{ data.grade }} / </span>
                    <span v-if="data.distance">{{ formatDistance(data.distance) }} / </span>
                    <span>{{ data.surface || 'コース未定' }}</span>
                  </div>
                </template>
              </Column>
              <Column field="raceStartTime" header="発走時刻" :sortable="false" style="width: 100px">
                <template #body="{ data }">
                  <span v-if="data.raceStartTime" class="font-medium">
                    {{ formatStartTime(data.raceStartTime) }}
                  </span>
                  <span v-else class="text-surface-400">未定</span>
                </template>
              </Column>
              <Column field="race_key" header="race_key" :sortable="false" style="width: 180px">
                <template #body="{ data }">
                  <Chip 
                    v-if="data.race_key" 
                    :label="data.race_key" 
                    severity="secondary" 
                    class="font-mono text-xs" 
                  />
                  <span v-else class="text-surface-400 text-xs">未設定</span>
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
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import { useRace } from '@/composables/useRace'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { convertVenueToId } from '@/router/routeCalculator'
import { getVenueNameFromId } from '@/entity'
import { RouteName } from '@/router/routeCalculator'
import { Timestamp } from 'firebase/firestore'

interface VenueRaceGroup {
  venue: string
  races: Race[]
  raceCount: number
}

const { navigateTo, navigateTo404, getParams, getQuery } = useNavigation()
const { races, fetchRaces } = useRace()

const dayRaces = ref<Race[]>([])
const dayName = ref('')
const expandedRows = ref<VenueRaceGroup[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// 競馬場ごとにレースをグループ化（DataTable用）
const venueGroups = computed<VenueRaceGroup[]>(() => {
  const grouped: { [key: string]: Race[] } = {}
  
  dayRaces.value.forEach(race => {
    // 後方互換性のため、racecourseまたはvenueを確認
    const venue = (race as any).racecourse || (race as any).venue || '不明'
    if (!grouped[venue]) {
      grouped[venue] = []
    }
    grouped[venue].push(race)
  })
  
  // レース番号でソート
  Object.keys(grouped).forEach(venue => {
    grouped[venue].sort((a, b) => (a.raceNumber || 0) - (b.raceNumber || 0))
  })
  
  // VenueRaceGroup形式に変換
  return Object.keys(grouped).map(venue => ({
    venue,
    races: grouped[venue],
    raceCount: grouped[venue].length
  }))
})

// 距離をフォーマット
const formatDistance = (distance: number | null | undefined): string => {
  if (!distance) return '距離未定'
  return `${distance.toLocaleString()}m`
}


// 発走時刻をフォーマット
const formatStartTime = (startTime: any): string => {
  if (!startTime) return '未定'
  
  // FirestoreのTimestampオブジェクトの場合
  if (startTime && typeof startTime === 'object' && 'seconds' in startTime) {
    const date = new Date(startTime.seconds * 1000)
    const hours = date.getHours()
    const minutes = date.getMinutes()
    return `${hours}時${minutes.toString().padStart(2, '0')}分`
  }
  
  // Dateオブジェクトの場合
  if (startTime instanceof Date) {
    const hours = startTime.getHours()
    const minutes = startTime.getMinutes()
    return `${hours}時${minutes.toString().padStart(2, '0')}分`
  }
  
  // 文字列の場合（"15:40"形式）
  if (typeof startTime === 'string') {
    const [hours, minutes] = startTime.split(':')
    if (hours && minutes) {
      return `${parseInt(hours)}時${minutes}分`
    }
  }
  
  return '未定'
}

// その日のJRAレース結果ページURLを生成
const getJRAUrlForDay = (): string => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const dayParam = params.day
  
  if (!yearParam || !monthParam || !dayParam) {
    return '#'
  }
  
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  const day = parseInt(dayParam)
  
  if (isNaN(year) || isNaN(month) || isNaN(day)) {
    return '#'
  }
  
  const monthStr = month.toString().padStart(2, '0')
  const dayStr = day.toString().padStart(2, '0')
  
  return `https://www.jra.go.jp/keiba/calendar${year}/${year}/${month}/${monthStr}${dayStr}.html`
}

// その日のレースデータを取得
const loadDayRaces = async (year: number, month: number, day: number) => {
  try {
    loading.value = true
    error.value = null
    
    // 指定された日付の範囲でデータを取得（UTC時刻で指定）
    // 日本時間（JST）で指定された日付をUTCに変換
    // JST = UTC + 9時間なので、UTCでは前日の15:00から当日の14:59:59まで
    const startDate = new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0))
    const endDate = new Date(Date.UTC(year, month - 1, day, 23, 59, 59, 999))
    
    await fetchRaces(startDate, endDate)
    
    // Firestoreのクエリで既にフィルタリングされているが、
    // タイムゾーンの問題を考慮して、再度フィルタリング
    const filteredRaces = races.value.filter(race => {
      // raceDateがTimestampの場合はtoDate()を使用、Dateの場合はそのまま使用
      let raceDateValue: Date
      if (race.raceDate instanceof Timestamp) {
        raceDateValue = race.raceDate.toDate()
      } else if (race.raceDate instanceof Date) {
        raceDateValue = race.raceDate
      } else if (race.raceDate && typeof race.raceDate === 'object' && 'toDate' in race.raceDate) {
        raceDateValue = (race.raceDate as any).toDate()
      } else if (race.raceDate && typeof race.raceDate === 'object' && 'seconds' in race.raceDate) {
        raceDateValue = new Date((race.raceDate as any).seconds * 1000)
      } else {
        // 後方互換性のため、dateフィールドも確認
        const dateValue = (race as any).date
        if (dateValue instanceof Timestamp) {
          raceDateValue = dateValue.toDate()
        } else if (dateValue instanceof Date) {
          raceDateValue = dateValue
        } else if (dateValue && typeof dateValue === 'object' && 'toDate' in dateValue) {
          raceDateValue = dateValue.toDate()
        } else if (dateValue && typeof dateValue === 'object' && 'seconds' in dateValue) {
          raceDateValue = new Date(dateValue.seconds * 1000)
        } else {
          return false // 日付が取得できない場合は除外
        }
      }
      
      // 日付を比較（年、月、日のみ）
      return raceDateValue.getUTCFullYear() === year && 
             raceDateValue.getUTCMonth() === month - 1 && 
             raceDateValue.getUTCDate() === day
    })
    
    console.log('取得したレース数:', races.value.length, 'フィルタリング後:', filteredRaces.length)
    
    if (filteredRaces.length > 0) {
      dayName.value = `${year}年${month}月${day}日`
      dayRaces.value = filteredRaces
    } else {
      // データがない場合でも、エラーではなく空の状態を表示
      dayName.value = `${year}年${month}月${day}日`
      dayRaces.value = []
    }
  } catch (err) {
    console.error('レースデータの取得に失敗しました:', err)
    error.value = err instanceof Error ? err.message : 'レースデータの取得に失敗しました'
    dayRaces.value = []
  } finally {
    loading.value = false
  }
}

// その日の特定競馬場のレースデータを取得
const loadDayRacesByPlace = async (year: number, month: number, day: number, placeId: string) => {
  try {
    // 指定された日付の範囲でデータを取得
    const startDate = new Date(year, month - 1, day, 0, 0, 0, 0)
    const endDate = new Date(year, month - 1, day, 23, 59, 59, 999)
    
    await fetchRaces(startDate, endDate)
    
    // 指定された日付と競馬場のレースをフィルタリング
    const filteredRaces = races.value.filter(race => {
      const raceDateValue = (race.raceDate || (race as any).date) instanceof Date 
        ? (race.raceDate || (race as any).date) 
        : ((race.raceDate || (race as any).date) as any).toDate()
      // 後方互換性のため、racecourseまたはvenueを確認
      const venue = (race as any).racecourse || (race as any).venue || '東京'
      const venueId = convertVenueToId(venue)
      return raceDateValue.getFullYear() === year && 
             raceDateValue.getMonth() === month - 1 && 
             raceDateValue.getDate() === day &&
             venueId === placeId
    })
    
    if (filteredRaces.length > 0) {
      dayName.value = `${year}年${month}月${day}日 - ${getVenueNameFromId(placeId as any)}`
      dayRaces.value = filteredRaces
    } else {
      navigateTo404()
    }
  } catch (err) {
    console.error('レースデータの取得に失敗しました:', err)
    navigateTo404()
  }
}

// レース選択時の処理
const selectRace = (race: Race) => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const dayParam = params.day
  
  if (!yearParam || !monthParam || !dayParam) {
    navigateTo404()
    return
  }
  
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  const day = parseInt(dayParam)
  
  if (isNaN(year) || isNaN(month) || isNaN(day)) {
    navigateTo404()
    return
  }
  
  // race_keyを使用（race.idがrace_keyになっている）
  const raceKey = race.race_key || race.id
  if (!raceKey) {
    console.error('race_keyが見つかりません', race)
    return
  }
  
  // 後方互換性のため、racecourseまたはvenueを確認
  const venue = (race as any).racecourse || (race as any).venue || '東京'
  const venueId = convertVenueToId(venue)
  navigateTo(RouteName.RACE_DETAIL, { year, month, placeId: venueId, raceId: raceKey })
}


onMounted(async () => {
  const params = getParams()
  const yearParam = params.year
  const monthParam = params.month
  const dayParam = params.day
  
  // 必須パラメータがなければ404ページに遷移
  if (!yearParam || !monthParam || !dayParam) {
    navigateTo404()
    return
  }
  
  // クエリパラメータからplaceIdを取得
  const placeId = getQuery('placeId')
  
  const year = parseInt(yearParam)
  const month = parseInt(monthParam)
  const day = parseInt(dayParam)
  
  if (isNaN(year) || isNaN(month) || isNaN(day)) {
    navigateTo404()
    return
  }
  
  // placeIdが指定されている場合は、その日のその競馬場のレース一覧を表示
  if (placeId) {
    await loadDayRacesByPlace(year, month, day, placeId as string)
  } else {
    // placeIdがない場合は、その日の全競馬場のレース一覧を表示
    await loadDayRaces(year, month, day)
  }
  
})

// 競馬場グループが変更されたら、すべて展開する
watch(venueGroups, (newGroups) => {
  if (newGroups.length > 0 && expandedRows.value.length === 0) {
    expandedRows.value = [...newGroups]
  }
}, { immediate: true })
</script>
