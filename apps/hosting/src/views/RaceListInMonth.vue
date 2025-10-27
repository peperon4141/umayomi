<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">{{ year }}年{{ month }}月のレース一覧</h1>
      <p class="text-gray-600 mt-1">{{ races.length }}件のレースが見つかりました</p>
    </div>

    <!-- カレンダー表示 -->
    <div v-if="viewMode === 'calendar'" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="bg-white rounded-lg shadow overflow-hidden calendar-container">
        <!-- カレンダーヘッダー -->
        <div class="bg-surface-900 text-surface-0 p-4">
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-bold">{{ year }}年{{ month }}月の競馬カレンダー</h2>
            <a 
              :href="getJRACalendarUrl()" 
              target="_blank" 
              rel="noopener noreferrer"
              class="flex items-center gap-2 px-3 py-2 bg-surface-0 text-surface-900 rounded-lg hover:bg-surface-100 transition-colors text-sm font-medium"
            >
              <i class="pi pi-external-link"></i>
              JRA公式ページ
            </a>
          </div>
        </div>
        
        <!-- 曜日ヘッダー -->
        <div class="calendar-grid bg-surface-100">
          <div v-for="day in weekDays" :key="day" 
               :class="getWeekDayClass(day)"
               class="calendar-cell calendar-header">
            {{ day }}
          </div>
        </div>
        
        <!-- カレンダーグリッド -->
        <div class="calendar-grid">
          <div v-for="date in calendarDates" :key="date.key"
               :class="getDateCellClass(date)"
               class="calendar-cell">
            
            <!-- 日付 -->
            <div class="text-sm font-medium mb-1">{{ date.day }}</div>
            
            <!-- レース情報 -->
            <div v-if="date.races && date.races.length > 0" class="space-y-1">
              <div v-for="race in date.races.slice(0, 2)" :key="race.id" 
                   class="text-xs cursor-pointer border-2 border-surface-200 hover:bg-surface-100 p-1 rounded"
                   @click="viewRaceDetail(race.id)">
                <div class="flex items-center gap-1 mb-1">
                  <Chip :label="race.racecourse" 
                        :severity="getVenueSeverity(race.racecourse)" 
                        size="small" />
                </div>
                <div class="text-surface-600 truncate">{{ race.raceName }}</div>
              </div>
              <div v-if="date.races.length > 2" class="text-xs text-surface-500">
                +{{ date.races.length - 2 }}レース
              </div>
            </div>
            
            <!-- 今日のマーカー -->
            <div v-if="isToday(date)" class="absolute top-1 right-1">
              <div class="w-2 h-2 bg-red-500 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 表示切り替えとアクションボタン -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex justify-between items-center">
        <!-- 表示切り替えボタン -->
        <div class="flex bg-surface-100 rounded-lg p-1">
          <Button
            :class="{ 'bg-surface-0 shadow-sm': viewMode === 'calendar' }"
            icon="pi pi-calendar"
            @click="viewMode = 'calendar'"
            text
            rounded
            size="small"
          />
          <Button
            :class="{ 'bg-surface-0 shadow-sm': viewMode === 'list' }"
            icon="pi pi-list"
            @click="viewMode = 'list'"
            text
            rounded
            size="small"
          />
        </div>
        
        <!-- アクションボタン -->
        <Button
          label="ダッシュボードに戻る"
          icon="pi pi-arrow-left"
          severity="secondary"
          @click="goToDashboard"
        />
      </div>
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

    <!-- レース一覧（リスト表示） -->
    <div v-else-if="viewMode === 'list' && races.length > 0" class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="race in races"
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
          </template>
        </Card>
      </div>
    </div>

  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Timestamp } from 'firebase/firestore'
import AppLayout from '@/layouts/AppLayout.vue'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Chip from 'primevue/chip'
import Skeleton from 'primevue/skeleton'
import { useRace } from '@/composables/useRace'

const router = useRouter()
const route = useRoute()

// ルートパラメータから年と月を取得
const year = computed(() => parseInt(route.params.year as string))
const month = computed(() => parseInt(route.params.month as string))

// useRace composableを使用
const { races, loading, error, fetchRaces } = useRace()

// 表示モード
const viewMode = ref<'calendar' | 'list'>('calendar')

// 曜日配列
const weekDays = ['月', '火', '水', '木', '金', '土', '日']

// カレンダー用の日付データ
const calendarDates = computed(() => {
  const dates = []
  const firstDay = new Date(year.value, month.value - 1, 1)
  const startDate = new Date(firstDay)
  
  // 月の最初の日が月曜日になるように調整
  const dayOfWeek = firstDay.getDay()
  const mondayOffset = dayOfWeek === 0 ? 6 : dayOfWeek - 1
  startDate.setDate(firstDay.getDate() - mondayOffset)
  
  // 6週間分の日付を生成
  for (let i = 0; i < 42; i++) {
    const currentDate = new Date(startDate)
    currentDate.setDate(startDate.getDate() + i)
    
    const day = currentDate.getDate()
    const isCurrentMonth = currentDate.getMonth() === month.value - 1
    const isCurrentYear = currentDate.getFullYear() === year.value
    
    // その日のレースを取得
    const dayRaces = races.value.filter(race => {
      // race.dateがTimestampの場合はtoDate()を使用、Dateの場合はそのまま使用
      const raceDate = race.date instanceof Timestamp ? race.date.toDate() : race.date
      return raceDate.getDate() === day && 
             raceDate.getMonth() === month.value - 1 && 
             raceDate.getFullYear() === year.value
    })
    
    dates.push({
      key: `${currentDate.getFullYear()}-${currentDate.getMonth() + 1}-${day}`,
      day,
      date: currentDate,
      isCurrentMonth: isCurrentMonth && isCurrentYear,
      races: dayRaces
    })
  }
  
  return dates
})

// レースデータを読み込み
const loadRaces = async () => {
  const startDate = new Date(year.value, month.value - 1, 1)
  const endDate = new Date(year.value, month.value, 0)
  await fetchRaces(startDate, endDate)
}

// グレードの重要度を取得
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

// 競馬場の重要度を取得
const getVenueSeverity = (venue: string) => {
  switch (venue) {
    case '東京':
      return 'info'
    case '京都':
      return 'success'
    case '新潟':
      return 'danger'
    case '中山':
      return 'warning'
    case '阪神':
      return 'help'
    case '中京':
      return 'contrast'
    default:
      return 'secondary'
  }
}

// 曜日のクラスを取得
const getWeekDayClass = (day: string) => {
  switch (day) {
    case '土':
      return 'bg-blue-100 text-blue-800'
    case '日':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-surface-100 text-surface-700'
  }
}

// 日付セルのクラスを取得
const getDateCellClass = (date: any) => {
  const classes = []
  
  if (!date.isCurrentMonth) {
    classes.push('bg-surface-50 text-surface-400')
  } else {
    classes.push('bg-white text-surface-900')
  }
  
  // 週末の背景色
  const dayOfWeek = date.date.getDay()
  if (dayOfWeek === 0) { // 日曜日
    classes.push('bg-red-50')
  } else if (dayOfWeek === 6) { // 土曜日
    classes.push('bg-blue-50')
  }
  
  return classes.join(' ')
}

// 今日かどうかを判定
const isToday = (date: any) => {
  const today = new Date()
  return date.date.getDate() === today.getDate() &&
         date.date.getMonth() === today.getMonth() &&
         date.date.getFullYear() === today.getFullYear()
}

// レース詳細ページに遷移
const viewRaceDetail = (raceId: string) => {
  console.log('viewRaceDetail called with raceId:', raceId)
  if (!raceId) {
    console.error('raceId is undefined or empty')
    return
  }
  router.push(`/race/${raceId}`)
}

// JRAのカレンダーページURLを生成
const getJRACalendarUrl = () => {
  const monthNames = ['', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
  const monthName = monthNames[month.value]
  return `https://www.jra.go.jp/keiba/calendar${year.value}/${monthName}.html`
}

// ダッシュボードに戻る
const goToDashboard = () => {
  router.push('/dashboard')
}

// コンポーネントマウント時にデータを読み込み
onMounted(() => {
  loadRaces()
})
</script>

<style scoped>
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0;
  width: 100%;
}

.calendar-cell {
  min-height: 6rem;
  padding: 0.5rem;
  border-right: 1px solid var(--p-surface-200);
  border-bottom: 1px solid var(--p-surface-200);
  position: relative;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
}

.calendar-cell:nth-child(7n) {
  border-right: none;
}

/* 曜日ヘッダー用のスタイル */
.calendar-header {
  min-height: 3rem;
  padding: 0.75rem 0.5rem;
  border-bottom: 2px solid var(--p-surface-200);
  justify-content: center;
  align-items: center;
  font-weight: 600;
  font-size: 0.875rem;
}

/* レスポンシブ対応 */
@media (max-width: 768px) {
  .calendar-cell {
    min-height: 4rem;
    padding: 0.25rem;
    font-size: 0.75rem;
  }
  
  .calendar-header {
    min-height: 2rem;
    padding: 0.5rem 0.25rem;
    font-size: 0.75rem;
  }
}

/* カレンダー全体の幅を固定 */
.calendar-container {
  width: 100%;
  overflow-x: auto;
}

.calendar-container .calendar-grid {
  min-width: 100%;
}
</style>