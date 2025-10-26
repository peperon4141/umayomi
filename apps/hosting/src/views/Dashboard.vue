<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">競馬レース結果ダッシュボード</h1>
      <p class="text-gray-600 mt-1">レース結果を確認できます</p>
    </div>

    <!-- 日付選択 -->
    <div class="mb-6 bg-white rounded-lg shadow p-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">日付範囲を選択</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">開始日</label>
          <Calendar 
            v-model="dateRange.startDate" 
            :maxDate="dateRange.endDate"
            placeholder="開始日を選択"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">終了日</label>
          <Calendar 
            v-model="dateRange.endDate" 
            :minDate="dateRange.startDate"
            placeholder="終了日を選択"
            class="w-full"
          />
        </div>
      </div>
      <div class="mt-4 flex gap-2">
        <Button 
          label="データを取得" 
          icon="pi pi-search" 
          @click="loadRaces"
          :loading="loading"
        />
        <Button 
          label="今月" 
          icon="pi pi-calendar" 
          severity="secondary"
          @click="setThisMonth"
        />
        <Button 
          label="先月" 
          icon="pi pi-calendar-minus" 
          severity="secondary"
          @click="setLastMonth"
        />
      </div>
    </div>

    <!-- JRAスクレイピングパネル -->
    <div class="mb-6">
      <JRAScrapingPanel @data-updated="loadRaces" />
    </div>

    <!-- 統計カード -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <Card class="bg-primary text-primary-contrast">
        <template #content>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-medium opacity-90">総レース数</h3>
              <p class="text-2xl font-bold">{{ totalRaces }}</p>
              <p class="text-sm opacity-90">今月の開催レース</p>
            </div>
            <div class="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
              <i class="pi pi-flag text-2xl"></i>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-green-600 text-white">
        <template #content>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-medium opacity-90">開催日数</h3>
              <p class="text-2xl font-bold">{{ raceDays.length }}</p>
              <p class="text-sm opacity-90">今月の開催日</p>
            </div>
            <div class="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
              <i class="pi pi-calendar text-2xl"></i>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-purple-600 text-white">
        <template #content>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-medium opacity-90">競馬場数</h3>
              <p class="text-2xl font-bold">{{ uniqueVenues.length }}</p>
              <p class="text-sm opacity-90">開催競馬場</p>
            </div>
            <div class="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
              <i class="pi pi-map-marker text-2xl"></i>
            </div>
          </div>
        </template>
      </Card>

      <Card class="bg-orange-600 text-white">
        <template #content>
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-medium opacity-90">G1レース</h3>
              <p class="text-2xl font-bold">{{ g1Races }}</p>
              <p class="text-sm opacity-90">最高グレード</p>
            </div>
            <div class="w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
              <i class="pi pi-star text-2xl"></i>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- フィルター -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <Panel header="フィルター" class="shadow-sm">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-2">競馬場</label>
            <InputGroup>
              <InputGroupAddon>
                <i class="pi pi-map-marker"></i>
              </InputGroupAddon>
              <Dropdown
                v-model="filters.racecourse"
                :options="racecourses"
                placeholder="すべて"
                class="w-full"
                @change="applyFilters"
              />
            </InputGroup>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-2">グレード</label>
            <InputGroup>
              <InputGroupAddon>
                <i class="pi pi-star"></i>
              </InputGroupAddon>
              <Dropdown
                v-model="filters.grade"
                :options="grades"
                placeholder="すべて"
                class="w-full"
                @change="applyFilters"
              />
            </InputGroup>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-surface-700 mb-2">コース</label>
            <InputGroup>
              <InputGroupAddon>
                <i class="pi pi-circle"></i>
              </InputGroupAddon>
              <Dropdown
                v-model="filters.surface"
                :options="surfaces"
                placeholder="すべて"
                class="w-full"
                @change="applyFilters"
              />
            </InputGroup>
          </div>
        </div>
        
        <!-- アクションボタン -->
        <div class="mt-4 flex flex-wrap gap-2">
          <Button
            label="フィルターリセット"
            icon="pi pi-refresh"
            severity="secondary"
            @click="resetFilters"
          />
          <Button
            label="サンプルデータ投入"
            icon="pi pi-database"
            severity="success"
            @click="handleSeedData"
          />
          <Button
            label="データクリア"
            icon="pi pi-trash"
            severity="danger"
            @click="handleClearData"
          />
        </div>
        
        <!-- アクティブフィルター表示 -->
        <div v-if="hasActiveFilters" class="mt-4 pt-4 border-t border-surface-200">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm text-surface-600">アクティブフィルター:</span>
            <Chip 
              v-if="filters.racecourse" 
              :label="`競馬場: ${filters.racecourse}`" 
              removable 
              @remove="filters.racecourse = undefined; applyFilters()"
            />
            <Chip 
              v-if="filters.grade" 
              :label="`グレード: ${filters.grade}`" 
              removable 
              @remove="filters.grade = undefined; applyFilters()"
            />
            <Chip 
              v-if="filters.surface" 
              :label="`コース: ${filters.surface}`" 
              removable 
              @remove="filters.surface = undefined; applyFilters()"
            />
          </div>
        </div>
      </Panel>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-6">
        <div class="text-center mb-8">
          <Skeleton width="300px" height="2rem" class="mx-auto mb-2" />
          <Skeleton width="200px" height="1rem" class="mx-auto" />
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card v-for="n in 6" :key="n" class="rounded-xl overflow-hidden">
            <template #header>
              <Skeleton width="100%" height="80px" />
            </template>
            <template #content>
              <div class="p-4 space-y-3">
                <Skeleton width="100%" height="1rem" />
                <Skeleton width="80%" height="1rem" />
                <Skeleton width="60%" height="1rem" />
              </div>
            </template>
            <template #footer>
              <Skeleton width="100%" height="40px" />
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- エラー -->
    <div v-else-if="error" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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
            label="再読み込み"
            icon="pi pi-refresh"
            @click="loadRaces"
          />
        </div>
      </div>
    </div>

    <!-- レース一覧 -->
    <div v-else-if="Object.keys(racesByDate).length > 0" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
      <div v-for="(dayRaces, date) in racesByDate" :key="date" class="mb-8">
        <div class="flex justify-between items-center mb-6 pb-3 border-b-2 border-red-500">
          <h2 class="text-2xl font-semibold text-gray-900">{{ date }}</h2>
          <Chip :label="`${dayRaces.length}レース`" size="small" severity="info" />
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card
            v-for="race in dayRaces"
            :key="race.id"
            class="rounded-xl overflow-hidden hover:shadow-lg transition-shadow duration-200"
          >
            <template #header>
              <div class="bg-surface-900 text-surface-0 p-4">
                <div class="flex justify-between items-center">
                  <h3 class="text-lg font-bold">{{ race.raceNumber }}R {{ race.raceName }}</h3>
                  <Chip :label="race.grade" :severity="getGradeSeverity(race.grade)" size="small" />
                </div>
                <div class="flex gap-2 mt-2">
                  <Chip :label="`${race.distance}m`" size="small" severity="secondary" />
                  <Chip :label="race.surface" size="small" severity="contrast" />
                  <Chip :label="race.weather" size="small" severity="info" />
                </div>
              </div>
            </template>
            <template #content>
              <div class="p-4">
                <div class="flex justify-between items-center mb-3">
                  <span class="text-sm text-surface-600">競馬場</span>
                  <span class="font-medium">{{ race.racecourse }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-surface-600">馬場状態</span>
                  <span class="font-medium">{{ race.trackCondition }}</span>
                </div>
              </div>
            </template>
            <template #footer>
                <Button
                  label="詳細を見る"
                  icon="pi pi-arrow-right"
                  class="w-full"
                  @click="viewRaceDetail(race.id)"
                />
                <!-- デバッグ情報 -->
                <div class="text-xs text-gray-500 mt-2">
                  ID: {{ race.id || 'undefined' }}
                </div>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- データなし -->
    <div v-else class="flex items-center justify-center min-h-96">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-gray-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">レースデータがありません</h3>
               <p class="text-gray-600 mb-6">10月分のレース結果が見つかりませんでした。</p>
        <Button
          label="データを再読み込み"
          icon="pi pi-refresh"
          @click="loadRaces"
        />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useRace } from '@/composables/useRace'
import AppLayout from '@/layouts/AppLayout.vue'
import JRAScrapingPanel from '@/components/JRAScrapingPanel.vue'
import { seedRaceData, clearRaceData } from '@/utils/sampleData'
import type { RaceFilters } from '../../../shared/race'

const router = useRouter()
const { 
  loading, 
  error, 
  racecourses, 
  grades, 
  surfaces, 
  racesByDate, 
  fetchOctoberRaces 
} = useRace()

const filters = ref<RaceFilters>({
  racecourse: undefined,
  grade: undefined,
  surface: undefined
})

const raceDays = ref<any[]>([])

// 日付範囲の管理
const dateRange = ref({
  startDate: new Date('2024-10-01'),
  endDate: new Date('2024-10-31')
})

const loadRaces = async () => {
  await fetchOctoberRaces()
  // raceDaysを更新 - racesByDateはオブジェクトなので配列に変換
  if (racesByDate.value) {
    raceDays.value = Object.values(racesByDate.value).flat()
  } else {
    raceDays.value = []
  }
}

// 日付範囲の設定
const setThisMonth = () => {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  dateRange.value = {
    startDate: firstDay,
    endDate: lastDay
  }
}

const setLastMonth = () => {
  const now = new Date()
  const firstDay = new Date(now.getFullYear(), now.getMonth() - 1, 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth(), 0)
  dateRange.value = {
    startDate: firstDay,
    endDate: lastDay
  }
}

const applyFilters = () => {
  loadRaces()
}

const resetFilters = () => {
  filters.value = {
    racecourse: undefined,
    grade: undefined,
    surface: undefined
  }
  loadRaces()
}

const hasActiveFilters = computed(() => {
  return filters.value.racecourse || filters.value.grade || filters.value.surface
})

// 統計データの計算
const totalRaces = computed(() => {
  return raceDays.value.reduce((total: number, day: any) => total + (day.races?.length || 0), 0)
})

const uniqueVenues = computed(() => {
  const venues = new Set()
  raceDays.value.forEach((day: any) => {
    if (day.venue) venues.add(day.venue)
  })
  return Array.from(venues)
})

const g1Races = computed(() => {
  let count = 0
  raceDays.value.forEach((day: any) => {
    if (day.races) {
      day.races.forEach((race: any) => {
        if (race.grade === 'GⅠ') count++
      })
    }
  })
  return count
})

const getGradeSeverity = (grade: string) => {
  switch (grade) {
    case 'GⅠ':
      return 'danger'
    case 'GⅡ':
      return 'warning'
    case 'GⅢ':
      return 'info'
    case 'オープン':
      return 'success'
    default:
      return 'secondary'
  }
}


const viewRaceDetail = (raceId: string) => {
  console.log('viewRaceDetail called with raceId:', raceId)
  if (!raceId) {
    console.error('raceId is undefined or empty')
    return
  }
  // レースIDから直接レース詳細ページに遷移
  router.push(`/race/${raceId}`)
}


const handleSeedData = async () => {
  await seedRaceData()
  await loadRaces()
}

const handleClearData = async () => {
  await clearRaceData()
  await loadRaces()
}

onMounted(() => {
  loadRaces()
})
</script>

