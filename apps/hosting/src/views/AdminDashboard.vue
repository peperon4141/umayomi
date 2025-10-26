<template>
  <div class="min-h-screen bg-surface-0">
    <!-- 管理画面ヘッダー -->
    <header class="bg-surface-0 shadow-sm border-b border-surface-border">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <!-- ロゴとタイトル -->
          <div class="flex items-center space-x-4">
            <div class="w-8 h-8 bg-primary text-primary-contrast rounded-lg flex items-center justify-center font-bold text-lg">
              管
            </div>
            <h1 class="text-xl font-bold text-surface-900">管理ダッシュボード</h1>
          </div>
          
          <!-- ユーザー情報とナビゲーション -->
          <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
              <Avatar 
                :label="user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'A'" 
                size="normal" 
                class="font-medium" 
                shape="circle"
                style="background-color: var(--p-purple-500); color: white;"
              />
              <div class="text-sm">
                <p class="font-medium text-surface-900">{{ user?.displayName || '管理者' }}</p>
                <p class="text-surface-500">{{ user?.email }}</p>
              </div>
            </div>
            
            <Button
              label="メインアプリに戻る"
              icon="pi pi-arrow-left"
              severity="secondary"
              size="small"
              @click="goToMainApp"
            />
            
            <Button
              label="ログアウト"
              icon="pi pi-sign-out"
              severity="danger"
              size="small"
              @click="handleLogout"
            />
          </div>
        </div>
      </div>
    </header>

    <!-- メインコンテンツ -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- ページヘッダー -->
      <div class="mb-8">
        <h2 class="text-3xl font-bold text-surface-900 mb-2">システム管理</h2>
        <p class="text-surface-600">競馬データの管理とCloud Functions実行</p>
      </div>

      <!-- 統計カード -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card class="bg-primary text-primary-contrast">
          <template #content>
            <div class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-primary-contrast text-sm font-medium opacity-80">総レース数</p>
                  <p class="text-3xl font-bold">{{ totalRaces }}</p>
                </div>
                <i class="pi pi-chart-line text-4xl text-primary-contrast opacity-60"></i>
              </div>
            </div>
          </template>
        </Card>

        <Card class="bg-green-600 text-white">
          <template #content>
            <div class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-white text-sm font-medium opacity-80">今月のレース</p>
                  <p class="text-3xl font-bold">{{ monthlyRaces }}</p>
                </div>
                <i class="pi pi-calendar text-4xl text-white opacity-60"></i>
              </div>
            </div>
          </template>
        </Card>

        <Card class="bg-purple-600 text-white">
          <template #content>
            <div class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-white text-sm font-medium opacity-80">アクティブユーザー</p>
                  <p class="text-3xl font-bold">{{ activeUsers }}</p>
                </div>
                <i class="pi pi-users text-4xl text-white opacity-60"></i>
              </div>
            </div>
          </template>
        </Card>

        <Card class="bg-orange-600 text-white">
          <template #content>
            <div class="p-6">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-white text-sm font-medium opacity-80">システム状態</p>
                  <p class="text-3xl font-bold">正常</p>
                </div>
                <i class="pi pi-check-circle text-4xl text-white opacity-60"></i>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- JRAスクレイピングパネル -->
      <div class="mb-8">
        <JRAScrapingPanel @data-updated="refreshData" />
      </div>

      <!-- Functions Log -->
      <div class="mb-8">
        <Card>
          <template #header>
            <div class="p-6 border-b border-surface-border">
              <h3 class="text-xl font-bold text-surface-900">Functions Log</h3>
              <p class="text-surface-600 mt-1">スクレイピング処理の実行履歴</p>
            </div>
          </template>
          <template #content>
            <div class="p-6">
              <!-- ローディング -->
              <div v-if="functionLogLoading" class="text-center py-8">
                <ProgressSpinner />
                <p class="mt-4 text-surface-600">ログを読み込み中...</p>
              </div>

              <!-- エラー -->
              <div v-else-if="functionLogError" class="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <i class="pi pi-exclamation-triangle text-red-500 text-4xl mb-4"></i>
                <h3 class="text-red-800 font-medium mb-2">エラーが発生しました</h3>
                <p class="text-red-600">{{ functionLogError }}</p>
              </div>

              <!-- ログ一覧 -->
              <div v-else-if="functionLogs.length > 0" class="space-y-4">
                <div v-for="log in functionLogs" :key="log.id" 
                     :class="log.success ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'"
                     class="border rounded-lg p-4">
                  <div class="flex justify-between items-start mb-2">
                    <div class="flex items-center gap-2">
                      <Chip 
                        :label="log.functionName" 
                        :severity="log.success ? 'success' : 'danger'"
                        size="small" 
                      />
                      <Chip 
                        :label="`${log.year}年${log.month}月`" 
                        severity="info"
                        size="small" 
                      />
                      <Chip 
                        v-if="log.executionTimeMs"
                        :label="`${log.executionTimeMs}ms`" 
                        severity="secondary"
                        size="small" 
                      />
                    </div>
                    <div class="text-sm text-surface-500">
                      {{ formatLogDate(log.timestamp) }}
                    </div>
                  </div>
                  
                  <p class="text-sm font-medium mb-2">{{ log.message }}</p>
                  
                  <div v-if="log.success && log.additionalData" class="text-sm text-surface-600 space-y-1">
                    <div v-for="(value, key) in log.additionalData" :key="key">
                      {{ formatAdditionalDataKey(key) }}: {{ formatAdditionalDataValue(value) }}
                    </div>
                  </div>
                  
                  <div v-else-if="log.error" class="text-sm text-red-600">
                    エラー: {{ log.error }}
                  </div>
                </div>
              </div>

              <!-- データなし -->
              <div v-else class="text-center py-8">
                <i class="pi pi-list text-6xl text-surface-400 mb-4"></i>
                <h3 class="text-xl font-semibold text-surface-900 mb-2">ログがありません</h3>
                <p class="text-surface-600">スクレイピング処理を実行すると、ここにログが表示されます。</p>
              </div>
            </div>
          </template>
        </Card>
      </div>

      <!-- 管理機能 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- データ管理 -->
        <Card>
          <template #header>
            <div class="p-6 border-b border-surface-border">
              <h3 class="text-xl font-bold text-surface-900">データ管理</h3>
              <p class="text-surface-600 mt-1">レースデータの管理と操作</p>
            </div>
          </template>
          <template #content>
            <div class="p-6 space-y-4">

              <div class="flex items-center justify-between p-4 bg-surface-50 rounded-lg">
                <div>
                  <h4 class="font-semibold text-surface-900">サンプルデータ投入</h4>
                  <p class="text-sm text-surface-600">テスト用データを生成</p>
                </div>
                <Button
                  label="実行"
                  icon="pi pi-database"
                  severity="success"
                  @click="handleSeedData"
                />
              </div>

              <div class="flex items-center justify-between p-4 bg-surface-50 rounded-lg">
                <div>
                  <h4 class="font-semibold text-surface-900">データクリア</h4>
                  <p class="text-sm text-surface-600">全データを削除</p>
                </div>
                <Button
                  label="実行"
                  icon="pi pi-trash"
                  severity="danger"
                  @click="handleClearData"
                />
              </div>
            </div>
          </template>
        </Card>

        <!-- システム管理 -->
        <Card>
          <template #header>
            <div class="p-6 border-b border-surface-border">
              <h3 class="text-xl font-bold text-surface-900">システム管理</h3>
              <p class="text-surface-600 mt-1">システムの監視と設定</p>
            </div>
          </template>
          <template #content>
            <div class="p-6 space-y-4">
              <div class="p-4 bg-surface-50 rounded-lg">
                <h4 class="font-semibold text-surface-900 mb-2">システム情報</h4>
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span class="text-surface-600">バージョン:</span>
                    <span class="font-medium">v1.0.0</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-600">最終更新:</span>
                    <span class="font-medium">{{ lastUpdate }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span class="text-surface-600">ステータス:</span>
                    <Badge label="正常" severity="success" />
                  </div>
                </div>
              </div>

              <div class="p-4 bg-surface-50 rounded-lg">
                <h4 class="font-semibold text-surface-900 mb-2">ログ監視</h4>
                <p class="text-sm text-surface-600 mb-3">システムログの確認と監視</p>
                <Button
                  label="ログを確認"
                  icon="pi pi-file"
                  severity="warning"
                  size="small"
                />
              </div>

              <div class="p-4 bg-surface-50 rounded-lg">
                <h4 class="font-semibold text-surface-900 mb-2">バックアップ</h4>
                <p class="text-sm text-surface-600 mb-3">データのバックアップとリストア</p>
                <div class="flex gap-2">
                  <Button
                    label="バックアップ"
                    icon="pi pi-download"
                    severity="secondary"
                    size="small"
                  />
                  <Button
                    label="リストア"
                    icon="pi pi-upload"
                    severity="secondary"
                    size="small"
                  />
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>

    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useRace } from '@/composables/useRace'
import { useFunctionLog } from '@/composables/useFunctionLog'
import JRAScrapingPanel from '@/components/JRAScrapingPanel.vue'
import { seedRaceData, clearRaceData } from '@/utils/sampleData'
import { useToast } from 'primevue/usetoast'
import { getCurrentYear, getCurrentMonth } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Chip from 'primevue/chip'
import ProgressSpinner from 'primevue/progressspinner'
import Avatar from 'primevue/avatar'

const router = useRouter()
const { user, signOut } = useAuth()
const { races, fetchOctoberRaces } = useRace()
const { logs: functionLogs, loading: functionLogLoading, error: functionLogError } = useFunctionLog()
const toast = useToast()

// 統計データ
const totalRaces = ref(0)
const monthlyRaces = ref(0)
const activeUsers = ref(1)
const lastUpdate = ref(`${getCurrentYear()}年${getCurrentMonth()}月15日`)


// ログ日付フォーマット関数
const formatLogDate = (date: Date) => {
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// additionalDataのキーを日本語に変換
const formatAdditionalDataKey = (key: string) => {
  const keyMap: Record<string, string> = {
    racesCount: 'レース数',
    savedCount: '保存数',
    calendarRacesCount: 'カレンダーレース',
    raceResultsCount: 'レース結果',
    totalRacesCount: '総レース数',
    processedDates: '処理日数',
    url: 'URL',
    calendarUrl: 'カレンダーURL',
    executionTimeMs: '実行時間'
  }
  return keyMap[key] || key
}

// additionalDataの値をフォーマット
const formatAdditionalDataValue = (value: any) => {
  if (Array.isArray(value)) {
    return `${value.length}件`
  }
  if (typeof value === 'number') {
    if (value > 1000) {
      return `${value}ms`
    }
    return `${value}件`
  }
  if (typeof value === 'string') {
    return value
  }
  return String(value)
}

const goToMainApp = () => {
  router.push('/dashboard')
}

const handleLogout = async () => {
  try {
    await signOut()
    router.push('/')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}

const refreshData = async () => {
  await fetchOctoberRaces()
}

const handleSeedData = async () => {
  await seedRaceData()
  toast.add({
    severity: 'success',
    summary: 'サンプルデータ投入完了',
    detail: 'テスト用データを生成しました',
    life: 3000
  })
}

const handleClearData = async () => {
  await clearRaceData()
  toast.add({
    severity: 'success',
    summary: 'データクリア完了',
    detail: '全データを削除しました',
    life: 3000
  })
}

onMounted(async () => {
  // Firestoreからレースデータを取得
  await fetchOctoberRaces()
  
  // 統計データの計算
  totalRaces.value = races.value.length
  monthlyRaces.value = races.value.length
  activeUsers.value = 1
})
</script>