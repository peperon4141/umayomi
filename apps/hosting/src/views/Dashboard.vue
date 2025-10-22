<template>
  <div class="min-h-screen bg-gray-50">
    <!-- ヘッダー -->
    <div class="bg-white border-b border-gray-200 shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-6">
          <div>
            <h1 class="text-3xl font-bold text-gray-900">競馬レース結果ダッシュボード</h1>
                   <p class="text-gray-600 mt-1">8月分のレース結果を確認できます</p>
          </div>
          <Button
            label="ログアウト"
            icon="pi pi-sign-out"
            severity="secondary"
            @click="handleLogout"
          />
        </div>
      </div>
    </div>

    <!-- フィルター -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">競馬場</label>
            <Dropdown
              v-model="filters.racecourse"
              :options="racecourses"
              placeholder="すべて"
              class="w-full"
              @change="applyFilters"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">グレード</label>
            <Dropdown
              v-model="filters.grade"
              :options="grades"
              placeholder="すべて"
              class="w-full"
              @change="applyFilters"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">コース</label>
            <Dropdown
              v-model="filters.surface"
              :options="surfaces"
              placeholder="すべて"
              class="w-full"
              @change="applyFilters"
            />
          </div>
          
                 <div class="flex gap-2">
                   <Button
                     label="フィルターリセット"
                     icon="pi pi-refresh"
                     severity="secondary"
                     @click="resetFilters"
                   />
                   <Button
                     label="JRAスクレイピング実行"
                     icon="pi pi-cloud-download"
                     severity="info"
                     @click="handleJraScraping"
                     :loading="scrapingLoading"
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
        </div>
      </div>
    </div>

    <!-- ローディング -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-20">
      <ProgressSpinner />
      <p class="mt-4 text-lg text-gray-600">レースデータを読み込み中...</p>
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
          <span class="bg-blue-100 text-blue-800 text-sm font-medium px-3 py-1 rounded-full">
            {{ dayRaces.length }}レース
          </span>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <RaceCard
            v-for="race in dayRaces"
            :key="race.id"
            :race="race"
          />
        </div>
      </div>
    </div>

    <!-- データなし -->
    <div v-else class="flex items-center justify-center min-h-96">
      <div class="text-center">
        <i class="pi pi-calendar text-6xl text-gray-400 mb-4"></i>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">レースデータがありません</h3>
               <p class="text-gray-600 mb-6">8月分のレース結果が見つかりませんでした。</p>
        <Button
          label="データを再読み込み"
          icon="pi pi-refresh"
          @click="loadRaces"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useRace } from '@/composables/useRace'
import RaceCard from '@/components/RaceCard.vue'
import { seedRaceData, clearRaceData } from '@/utils/sampleData'
import type { RaceFilters } from '@/types/race'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const toast = useToast()
const { signOut } = useAuth()
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

const scrapingLoading = ref(false)

const loadRaces = async () => {
  await fetchOctoberRaces(filters.value)
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

const handleLogout = async () => {
  await signOut()
  router.push('/')
}

const handleJraScraping = async () => {
  scrapingLoading.value = true
  
  try {
    // Cloud Functionsのエンドポイントを呼び出し
          const response = await fetch('http://127.0.0.1:5101/umayomi-dev/us-central1/scrapeJRAData', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({})
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'スクレイピング完了',
        detail: `${result.savedCount}件のレースデータを取得しました`,
        life: 5000
      })
      
      // データを再読み込み
      await loadRaces()
    } else {
      throw new Error(result.error || 'スクレイピングに失敗しました')
    }
  } catch (error) {
    console.error('JRA scraping error:', error)
    toast.add({
      severity: 'error',
      summary: 'スクレイピングエラー',
      detail: error instanceof Error ? error.message : '不明なエラーが発生しました',
      life: 5000
    })
  } finally {
    scrapingLoading.value = false
  }
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

