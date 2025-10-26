<template>
  <Card class="w-full">
    <template #title>
      <div class="flex items-center gap-2">
        <i class="pi pi-cloud-download text-primary"></i>
        <span>JRAデータスクレイピング</span>
      </div>
    </template>
    
    <template #content>
      <div class="space-y-4">
        <!-- カレンダーデータスクレイピング -->
        <div class="border border-surface-200 rounded-lg p-4">
          <h4 class="text-lg font-semibold mb-3 text-surface-800">
            <i class="pi pi-calendar text-primary mr-2"></i>
            カレンダーデータ取得
          </h4>
          <p class="text-sm text-surface-600 mb-4">
            指定した年・月のJRAカレンダーデータを取得します
          </p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">年</label>
              <InputNumber
                v-model="calendarParams.year"
                :min="2020"
                :max="2030"
                placeholder="2025"
                class="w-full"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">月</label>
              <Dropdown
                v-model="calendarParams.month"
                :options="monthOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="月を選択"
                class="w-full"
              />
            </div>
          </div>
          
          <Button
            label="カレンダーデータ取得"
            icon="pi pi-calendar"
            severity="info"
            @click="handleCalendarScraping"
            :loading="calendarLoading"
            :disabled="!calendarParams.year || !calendarParams.month"
            class="w-full"
          />
        </div>
        
        <!-- レース結果データスクレイピング -->
        <div class="border border-surface-200 rounded-lg p-4">
          <h4 class="text-lg font-semibold mb-3 text-surface-800">
            <i class="pi pi-trophy text-primary mr-2"></i>
            レース結果データ取得
          </h4>
          <p class="text-sm text-surface-600 mb-4">
            指定した日付のJRAレース結果データを取得します
          </p>
          
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">年</label>
              <InputNumber
                v-model="raceResultParams.year"
                :min="2020"
                :max="2030"
                placeholder="2025"
                class="w-full"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">月</label>
              <Dropdown
                v-model="raceResultParams.month"
                :options="monthOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="月を選択"
                class="w-full"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">日</label>
              <InputNumber
                v-model="raceResultParams.day"
                :min="1"
                :max="31"
                placeholder="13"
                class="w-full"
              />
            </div>
          </div>
          
          <Button
            label="レース結果データ取得"
            icon="pi pi-trophy"
            severity="success"
            @click="handleRaceResultScraping"
            :loading="raceResultLoading"
            :disabled="!raceResultParams.year || !raceResultParams.month || !raceResultParams.day"
            class="w-full"
          />
        </div>
        
        <!-- 一括データ取得 -->
        <div class="border border-surface-200 rounded-lg p-4">
          <h4 class="text-lg font-semibold mb-3 text-surface-800">
            <i class="pi pi-download text-primary mr-2"></i>
            一括データ取得
          </h4>
          <p class="text-sm text-surface-600 mb-4">
            指定した年・月のカレンダーデータと各日程のレース結果データを一括で取得します
          </p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">年</label>
              <InputNumber
                v-model="bulkParams.year"
                :min="2020"
                :max="2030"
                placeholder="2025"
                class="w-full"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-700 mb-2">月</label>
              <Dropdown
                v-model="bulkParams.month"
                :options="monthOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="月を選択"
                class="w-full"
              />
            </div>
          </div>
          
          <Button
            label="一括データ取得"
            icon="pi pi-download"
            severity="warning"
            @click="handleBulkScraping"
            :loading="bulkLoading"
            :disabled="!bulkParams.year || !bulkParams.month"
            class="w-full"
          />
        </div>
        
        <!-- クイックアクション -->
        <div class="border border-surface-200 rounded-lg p-4">
          <h4 class="text-lg font-semibold mb-3 text-surface-800">
            <i class="pi pi-bolt text-primary mr-2"></i>
            クイックアクション
          </h4>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
            <Button
              label="今月のカレンダー"
              icon="pi pi-calendar"
              severity="secondary"
              @click="setCurrentMonth"
              class="w-full"
            />
            <Button
              label="今日のレース結果"
              icon="pi pi-trophy"
              severity="secondary"
              @click="setToday"
              class="w-full"
            />
            <Button
              label="今月の一括取得"
              icon="pi pi-download"
              severity="secondary"
              @click="setCurrentMonthBulk"
              class="w-full"
            />
          </div>
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useToast } from 'primevue/usetoast'

const toast = useToast()

// パラメータ
const calendarParams = ref({
  year: 2025,
  month: 10
})

const raceResultParams = ref({
  year: 2025,
  month: 10,
  day: 13
})

const bulkParams = ref({
  year: 2025,
  month: 10
})

// ローディング状態
const calendarLoading = ref(false)
const raceResultLoading = ref(false)
const bulkLoading = ref(false)

// 月の選択肢
const monthOptions = computed(() => [
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

// カレンダーデータスクレイピング
const handleCalendarScraping = async () => {
  calendarLoading.value = true
  
  try {
    const response = await fetch(
      `http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendar?year=${calendarParams.value.year}&month=${calendarParams.value.month}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'カレンダーデータ取得完了',
        detail: `${result.racesCount}件のレースデータを取得しました`,
        life: 5000
      })
      
      // 親コンポーネントにイベントを発火
      emit('data-updated')
    } else {
      throw new Error(result.error || 'カレンダーデータの取得に失敗しました')
    }
  } catch (error) {
    console.error('Calendar scraping error:', error)
    toast.add({
      severity: 'error',
      summary: 'カレンダーデータ取得エラー',
      detail: error instanceof Error ? error.message : '不明なエラーが発生しました',
      life: 5000
    })
  } finally {
    calendarLoading.value = false
  }
}

// レース結果データスクレイピング
const handleRaceResultScraping = async () => {
  raceResultLoading.value = true
  
  try {
    const response = await fetch(
      `http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRARaceResult?year=${raceResultParams.value.year}&month=${raceResultParams.value.month}&day=${raceResultParams.value.day}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'レース結果データ取得完了',
        detail: `${result.racesCount}件のレース結果データを取得しました`,
        life: 5000
      })
      
      // 親コンポーネントにイベントを発火
      emit('data-updated')
    } else {
      throw new Error(result.error || 'レース結果データの取得に失敗しました')
    }
  } catch (error) {
    console.error('Race result scraping error:', error)
    toast.add({
      severity: 'error',
      summary: 'レース結果データ取得エラー',
      detail: error instanceof Error ? error.message : '不明なエラーが発生しました',
      life: 5000
    })
  } finally {
    raceResultLoading.value = false
  }
}

// 一括データ取得
const handleBulkScraping = async () => {
  bulkLoading.value = true
  
  try {
    const response = await fetch(
      `http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendarWithRaceResults?year=${bulkParams.value.year}&month=${bulkParams.value.month}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: '一括データ取得完了',
        detail: `カレンダー: ${result.calendarRacesCount}件、レース結果: ${result.raceResultsCount}件、合計: ${result.totalRacesCount}件のデータを取得しました`,
        life: 5000
      })
      
      // 親コンポーネントにイベントを発火
      emit('data-updated')
    } else {
      throw new Error(result.error || '一括データの取得に失敗しました')
    }
  } catch (error) {
    console.error('Bulk scraping error:', error)
    toast.add({
      severity: 'error',
      summary: '一括データ取得エラー',
      detail: error instanceof Error ? error.message : '不明なエラーが発生しました',
      life: 5000
    })
  } finally {
    bulkLoading.value = false
  }
}

// クイックアクション
const setCurrentMonth = () => {
  const now = new Date()
  calendarParams.value = {
    year: now.getFullYear(),
    month: now.getMonth() + 1
  }
}

const setToday = () => {
  const now = new Date()
  raceResultParams.value = {
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    day: now.getDate()
  }
}

const setCurrentMonthBulk = () => {
  const now = new Date()
  bulkParams.value = {
    year: now.getFullYear(),
    month: now.getMonth() + 1
  }
}

// イベント発火
const emit = defineEmits<{
  'data-updated': []
}>()
</script>
