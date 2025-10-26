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

      <!-- Functions実行履歴 -->
      <Card class="mt-8">
        <template #header>
          <div class="p-6 border-b border-surface-border">
            <div class="flex justify-between items-center">
              <div>
                <h3 class="text-xl font-bold text-surface-900">Functions実行履歴</h3>
                <p class="text-surface-600 mt-1">Cloud Functionsの実行ログ</p>
              </div>
              <Button
                label="更新"
                icon="pi pi-refresh"
                severity="secondary"
                size="small"
                @click="refreshLogs"
                :loading="loading"
              />
            </div>
          </div>
        </template>
        <template #content>
          <div class="p-6">
            <DataTable
              :value="logs"
              :loading="loading"
              :paginator="true"
              :rows="pageSize"
              :totalRecords="totalCount"
              :lazy="true"
              @page="onPageChange"
              paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
              :rowsPerPageOptions="[5, 10, 20, 50]"
              currentPageReportTemplate="全 {totalRecords} 件中 {first} - {last} 件を表示"
              class="p-datatable-sm"
            >
              <Column field="functionName" header="関数名" :sortable="true">
                <template #body="{ data }">
                  <div class="flex items-center space-x-2">
                    <i :class="getFunctionIcon(data.functionName)" class="text-lg"></i>
                    <span class="font-medium">{{ getFunctionDisplayName(data.functionName) }}</span>
                  </div>
                </template>
              </Column>
              
              <Column field="status" header="ステータス" :sortable="true">
                <template #body="{ data }">
                  <Badge 
                    :label="data.status === 'success' ? '成功' : '失敗'"
                    :severity="data.status === 'success' ? 'success' : 'danger'"
                  />
                </template>
              </Column>
              
              <Column field="executedAt" header="実行日時" :sortable="true">
                <template #body="{ data }">
                  <span class="text-sm">
                    {{ formatDate(data.executedAt) }}
                  </span>
                </template>
              </Column>
              
              <Column field="metadata.duration" header="実行時間" :sortable="true">
                <template #body="{ data }">
                  <span class="text-sm text-surface-600">
                    {{ data.metadata?.duration ? `${data.metadata.duration}ms` : '-' }}
                  </span>
                </template>
              </Column>
              
              <Column header="詳細">
                <template #body="{ data }">
                  <Button
                    icon="pi pi-eye"
                    severity="secondary"
                    size="small"
                    @click="showLogDetail(data)"
                    v-tooltip.top="'詳細を表示'"
                  />
                </template>
              </Column>
            </DataTable>
          </div>
        </template>
      </Card>
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
// ローカル型定義
interface FunctionLog {
  id: string
  functionName: string
  status: 'success' | 'failure'
  executedAt: any
  metadata?: {
    duration?: number
    errorMessage?: string
    responseData?: any
    method?: string
    url?: string
    [key: string]: any
  }
}

const router = useRouter()
const { user, signOut } = useAuth()
const { races, fetchOctoberRaces } = useRace()
const { logs, loading, totalCount, pageSize, fetchLogs, onPageChange, refreshLogs } = useFunctionLog()
const toast = useToast()

// 統計データ
const totalRaces = ref(0)
const monthlyRaces = ref(0)
const activeUsers = ref(1)
const lastUpdate = ref(`${getCurrentYear()}年${getCurrentMonth()}月15日`)

// ローディング状態

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
  await refreshLogs()
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

// Functions実行履歴の表示用関数
const getFunctionIcon = (functionName: string) => {
  const iconMap: Record<string, string> = {
    'helloWorld': 'pi pi-check-circle text-primary',
    'scrapeJRAData': 'pi pi-cloud-download text-green-500',
    'manualJraScraping': 'pi pi-cog text-orange-500',
    'scheduledJraScraping': 'pi pi-clock text-purple-500',
    'setAdminRole': 'pi pi-user text-primary'
  }
  return iconMap[functionName] || 'pi pi-code text-surface-500'
}

const getFunctionDisplayName = (functionName: string) => {
  const nameMap: Record<string, string> = {
    'helloWorld': 'Hello World',
    'scrapeJRAData': 'JRAスクレイピング',
    'manualJraScraping': '手動JRAスクレイピング',
    'scheduledJraScraping': '定期JRAスクレイピング',
    'setAdminRole': '管理者権限設定'
  }
  return nameMap[functionName] || functionName
}

const formatDate = (timestamp: any) => {
  if (!timestamp) return '-'
  
  // Firestore Timestampの場合
  if (timestamp.toDate) {
    return timestamp.toDate().toLocaleString('ja-JP')
  }
  
  // Dateオブジェクトの場合
  if (timestamp instanceof Date) {
    return timestamp.toLocaleString('ja-JP')
  }
  
  // 文字列の場合
  return new Date(timestamp).toLocaleString('ja-JP')
}

const showLogDetail = (log: FunctionLog) => {
  const detail = {
    functionName: getFunctionDisplayName(log.functionName),
    status: log.status === 'success' ? '成功' : '失敗',
    executedAt: formatDate(log.executedAt),
    duration: log.metadata?.duration ? `${log.metadata.duration}ms` : '-',
    method: log.metadata?.method || '-',
    url: log.metadata?.url || '-',
    errorMessage: log.metadata?.errorMessage || '-',
    responseData: log.metadata?.responseData ? JSON.stringify(log.metadata.responseData, null, 2) : '-'
  }
  
  toast.add({
    severity: 'info',
    summary: '実行ログ詳細',
    detail: `関数: ${detail.functionName}\nステータス: ${detail.status}\n実行日時: ${detail.executedAt}\n実行時間: ${detail.duration}\nメソッド: ${detail.method}\nURL: ${detail.url}\nエラー: ${detail.errorMessage}\nレスポンス: ${detail.responseData}`,
    life: 10000
  })
}

onMounted(async () => {
  // Firestoreからレースデータを取得
  await fetchOctoberRaces()
  
  // 統計データの計算
  totalRaces.value = races.value.length
  monthlyRaces.value = races.value.length
  activeUsers.value = 1
  
  // Functions実行履歴を取得
  await fetchLogs()
})
</script>