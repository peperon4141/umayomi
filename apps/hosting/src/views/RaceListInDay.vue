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
    <div v-if="loading" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <i class="pi pi-spin pi-spinner text-4xl text-surface-500 mb-4"></i>
        <p class="text-surface-600">レースデータを読み込み中...</p>
      </div>
    </div>

    <!-- エラー -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <i class="pi pi-exclamation-triangle text-red-500 text-4xl mb-4"></i>
        <h3 class="text-red-800 font-medium mb-2">エラーが発生しました</h3>
        <p class="text-red-600">{{ error }}</p>
      </div>
    </div>

    <!-- データなし -->
    <div v-else-if="dayRaces.length === 0" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-surface-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-surface-900 mb-2">レースデータがありません</h3>
        <p class="text-surface-600">指定された日のレースが見つかりませんでした。</p>
      </div>
    </div>

    <!-- レース一覧（競馬場ごとにグループ化、横並び配置） -->
    <div v-else class="max-w-7xl mx-auto p-2">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 競馬場ごとのセクション -->
        <div 
          v-for="(venueRaces, venue) in racesByVenue" 
          :key="venue"
          class="bg-surface-0 rounded-lg shadow-sm overflow-hidden"
        >
          <!-- 競馬場ヘッダー -->
          <div class="bg-green-700 text-surface-0 px-6 py-3">
            <h2 class="text-lg font-bold">{{ venue }}</h2>
          </div>
          
          <!-- レーステーブル -->
          <div class="overflow-x-auto">
            <table class="w-full border-collapse">
              <thead>
                <tr class="bg-green-800 text-surface-0">
                  <th class="p-2 text-left font-semibold border-r border-green-900">レース<br>番号</th>
                  <th class="p-2 text-left font-semibold border-r border-green-900">レース名・条件</th>
                  <th class="p-2 text-left font-semibold">発走時刻</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="race in venueRaces" 
                  :key="race.id"
                  class="border-b border-surface-200 hover:bg-surface-50 cursor-pointer transition-colors"
                  @click="selectRace(race)"
                >
                  <!-- レース番号 -->
                  <td class="p-2 bg-green-50 border-r border-surface-200">
                    <div class="text-center">
                      <div class="text-lg font-bold text-green-800">{{ race.raceNumber }}</div>
                      <div class="text-xs text-green-600">レース</div>
                    </div>
                  </td>
                  
                  <!-- レース名・条件 -->
                  <td class="p-2 border-r border-surface-200">
                    <div class="space-y-1">
                      <div class="font-semibold text-surface-900">{{ race.raceName }}</div>
                      <div class="text-sm text-surface-600">
                        <span v-if="race.grade">{{ race.grade }} / </span>
                        <span v-if="race.distance">{{ formatDistance(race.distance) }} / </span>
                        <span>{{ race.surface || 'コース未定' }}</span>
                      </div>
                    </div>
                  </td>
                  
                  <!-- 発走時刻 -->
                  <td class="p-2 text-center">
                    <span v-if="race.startTime" class="font-medium text-surface-900">
                      {{ formatStartTime(race.startTime) }}
                    </span>
                    <span v-else class="text-surface-400">未定</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNavigation } from '@/composables/useNavigation'
import { useRace } from '@/composables/useRace'
import AppLayout from '@/layouts/AppLayout.vue'
import type { Race } from '../../../shared/race'
import { convertVenueToId } from '@/router/routeCalculator'
import { getVenueNameFromId } from '@/entity'
import { RouteName } from '@/router/routeCalculator'

const { navigateTo, navigateTo404, getParams, getQuery } = useNavigation()
const { races, loading, error, fetchOctoberRaces } = useRace()

const dayRaces = ref<Race[]>([])
const dayName = ref('')

// 競馬場ごとにレースをグループ化
const racesByVenue = computed(() => {
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
  
  return grouped
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
    await fetchOctoberRaces()
    
    // 指定された日付のレースをフィルタリング
    const filteredRaces = races.value.filter(race => {
      const raceDate = race.date instanceof Date ? race.date : (race.date as any).toDate()
      return raceDate.getFullYear() === year && 
             raceDate.getMonth() === month - 1 && 
             raceDate.getDate() === day
    })
    
    if (filteredRaces.length > 0) {
      dayName.value = `${year}年${month}月${day}日`
      dayRaces.value = filteredRaces
    } else {
      navigateTo404()
    }
  } catch (err) {
    console.error('レースデータの取得に失敗しました:', err)
    navigateTo404()
  }
}

// その日の特定競馬場のレースデータを取得
const loadDayRacesByPlace = async (year: number, month: number, day: number, placeId: string) => {
  try {
    await fetchOctoberRaces()
    
    // 指定された日付と競馬場のレースをフィルタリング
    const filteredRaces = races.value.filter(race => {
      const raceDate = race.date instanceof Date ? race.date : (race.date as any).toDate()
      // 後方互換性のため、racecourseまたはvenueを確認
  const venue = (race as any).racecourse || (race as any).venue || '東京'
  const venueId = convertVenueToId(venue)
      return raceDate.getFullYear() === year && 
             raceDate.getMonth() === month - 1 && 
             raceDate.getDate() === day &&
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
  
  // 後方互換性のため、racecourseまたはvenueを確認
  const venue = (race as any).racecourse || (race as any).venue || '東京'
  const venueId = convertVenueToId(venue)
  navigateTo(RouteName.RACE_DETAIL, { year, month, placeId: venueId, raceId: race.id })
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
</script>
