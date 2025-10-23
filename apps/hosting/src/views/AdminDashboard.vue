<template>
  <AppLayout>
    <!-- ページヘッダー -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold text-gray-900">管理ダッシュボード</h1>
      <p class="text-gray-600 mt-1">システム管理とCloud Functions実行</p>
    </div>

    <!-- メインコンテンツ -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- システム情報 -->
      <Card class="mb-8">
        <template #header>
          <div class="p-4 bg-gray-100">
            <h2 class="text-xl font-bold text-gray-900">システム情報</h2>
          </div>
        </template>
        <template #content>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="text-center p-4 bg-blue-50 rounded-lg">
                <div class="text-2xl font-bold text-blue-600">{{ systemInfo.functionsCount }}</div>
                <div class="text-sm text-gray-600">利用可能なFunctions</div>
              </div>
              <div class="text-center p-4 bg-green-50 rounded-lg">
                <div class="text-2xl font-bold text-green-600">{{ systemInfo.lastExecution }}</div>
                <div class="text-sm text-gray-600">最終実行時刻</div>
              </div>
              <div class="text-center p-4 bg-purple-50 rounded-lg">
                <div class="text-2xl font-bold text-purple-600">{{ systemInfo.totalExecutions }}</div>
                <div class="text-sm text-gray-600">総実行回数</div>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- ユーザー管理 -->
      <Card class="mb-8">
        <template #header>
          <div class="p-4 bg-gray-100">
            <h2 class="text-xl font-bold text-gray-900">ユーザー管理</h2>
          </div>
        </template>
        <template #content>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">ユーザーUID</label>
                <InputText
                  v-model="userUid"
                  placeholder="ユーザーのUIDを入力"
                  class="w-full"
                />
              </div>
              <div class="flex items-end">
                <Button
                  label="Adminロール付与"
                  icon="pi pi-user-plus"
                  severity="warning"
                  :loading="settingRole"
                  @click="setAdminRole"
                  class="w-full"
                />
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- Cloud Functions実行 -->
      <Card class="mb-8">
        <template #header>
          <div class="p-4 bg-gray-100">
            <h2 class="text-xl font-bold text-gray-900">Cloud Functions実行</h2>
          </div>
        </template>
        <template #content>
          <div class="p-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">利用可能なFunctions</label>
                  <Dropdown
                    v-model="selectedFunction"
                    :options="availableFunctions"
                    option-label="name"
                    option-value="value"
                    placeholder="Functionを選択"
                    class="w-full"
                  />
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">実行パラメータ（JSON）</label>
                  <Textarea
                    v-model="executionParams"
                    placeholder='{"key": "value"}'
                    rows="4"
                    class="w-full"
                  />
                </div>
                <Button
                  label="実行"
                  icon="pi pi-play"
                  severity="success"
                  :loading="executing"
                  @click="executeFunction"
                  class="w-full"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">実行結果</label>
                <div class="bg-gray-100 p-4 rounded-lg min-h-[200px] max-h-[400px] overflow-auto">
                  <pre class="text-sm text-gray-800 whitespace-pre-wrap">{{ executionResult }}</pre>
                </div>
              </div>
            </div>
          </div>
        </template>
      </Card>

      <!-- 実行履歴 -->
      <Card>
        <template #header>
          <div class="p-4 bg-gray-100 flex justify-between items-center">
            <h2 class="text-xl font-bold text-gray-900">実行履歴</h2>
            <Button
              label="履歴を更新"
              icon="pi pi-refresh"
              severity="secondary"
              size="small"
              @click="refreshHistory"
            />
          </div>
        </template>
        <template #content>
          <div class="p-4">
            <DataTable
              :value="executionHistory"
              :paginator="true"
              :rows="10"
              :loading="loadingHistory"
              class="p-datatable-sm"
            >
              <Column field="timestamp" header="実行時刻" sortable>
                <template #body="{ data }">
                  {{ formatTimestamp(data.timestamp) }}
                </template>
              </Column>
              <Column field="functionName" header="Function名" sortable />
              <Column field="status" header="ステータス" sortable>
                <template #body="{ data }">
                  <Badge
                    :value="data.status"
                    :severity="getStatusSeverity(data.status)"
                  />
                </template>
              </Column>
              <Column field="duration" header="実行時間" sortable>
                <template #body="{ data }">
                  {{ data.duration }}ms
                </template>
              </Column>
              <Column field="result" header="結果" sortable>
                <template #body="{ data }">
                  <Button
                    label="詳細"
                    icon="pi pi-eye"
                    size="small"
                    severity="info"
                    @click="showExecutionDetail(data)"
                  />
                </template>
              </Column>
            </DataTable>
          </div>
        </template>
      </Card>
    </div>

    <!-- 実行詳細ダイアログ -->
    <Dialog
      v-model:visible="showDetailDialog"
      header="実行詳細"
      :modal="true"
      :style="{ width: '80vw' }"
    >
      <div v-if="selectedExecution" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">実行時刻</label>
          <p class="text-gray-900">{{ formatTimestamp(selectedExecution.timestamp) }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Function名</label>
          <p class="text-gray-900">{{ selectedExecution.functionName }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">ステータス</label>
          <Badge
            :value="selectedExecution.status"
            :severity="getStatusSeverity(selectedExecution.status)"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">実行時間</label>
          <p class="text-gray-900">{{ selectedExecution.duration }}ms</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">実行パラメータ</label>
          <pre class="bg-gray-100 p-3 rounded text-sm">{{ JSON.stringify(selectedExecution.params, null, 2) }}</pre>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">実行結果</label>
          <pre class="bg-gray-100 p-3 rounded text-sm max-h-96 overflow-auto">{{ JSON.stringify(selectedExecution.result, null, 2) }}</pre>
        </div>
      </div>
    </Dialog>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import AppLayout from '@/layouts/AppLayout.vue'
import { useToast } from 'primevue/usetoast'

const router = useRouter()
const toast = useToast()
const { isAdmin } = useAuth()

// 管理者権限チェック
if (!isAdmin.value) {
  router.push('/dashboard')
}

// システム情報
const systemInfo = ref({
  functionsCount: 2,
  lastExecution: '未実行',
  totalExecutions: 0
})

// 利用可能なFunctions
const availableFunctions = ref([
  { name: 'Hello World', value: 'helloWorld' },
  { name: 'JRA スクレイピング', value: 'scrapeJRAData' }
])

// ユーザー管理
const userUid = ref('')
const settingRole = ref(false)

// 実行関連
const selectedFunction = ref('')
const executionParams = ref('{}')
const executing = ref(false)
const executionResult = ref('')

// 実行履歴
const executionHistory = ref<any[]>([])
const loadingHistory = ref(false)
const showDetailDialog = ref(false)
const selectedExecution = ref<any>(null)

// Adminロール付与
const setAdminRole = async () => {
  if (!userUid.value.trim()) {
    toast.add({
      severity: 'warn',
      summary: '警告',
      detail: 'ユーザーUIDを入力してください',
      life: 3000
    })
    return
  }

  settingRole.value = true

  try {
    const response = await fetch('http://127.0.0.1:5101/umayomi-dev/us-central1/setAdminRole', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ uid: userUid.value })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (result.success) {
      toast.add({
        severity: 'success',
        summary: 'ロール付与完了',
        detail: 'Adminロールが付与されました',
        life: 3000
      })
      userUid.value = ''
    } else {
      throw new Error(result.error || 'ロール付与に失敗しました')
    }

  } catch (error: any) {
    console.error('Admin role setting error:', error)
    toast.add({
      severity: 'error',
      summary: 'ロール付与エラー',
      detail: error instanceof Error ? error.message : '不明なエラーが発生しました',
      life: 5000
    })
  } finally {
    settingRole.value = false
  }
}

// 実行履歴を取得
const refreshHistory = async () => {
  loadingHistory.value = true
  try {
    // ローカルストレージから履歴を取得
    const history = localStorage.getItem('functionExecutionHistory')
    executionHistory.value = history ? JSON.parse(history) : []
  } catch (error: any) {
    console.error('履歴取得エラー:', error)
    toast.add({
      severity: 'error',
      summary: 'エラー',
      detail: '実行履歴の取得に失敗しました',
      life: 3000
    })
  } finally {
    loadingHistory.value = false
  }
}

// Function実行
const executeFunction = async () => {
  if (!selectedFunction.value) {
    toast.add({
      severity: 'warn',
      summary: '警告',
      detail: 'Functionを選択してください',
      life: 3000
    })
    return
  }

  executing.value = true
  executionResult.value = ''

  try {
    const startTime = Date.now()
    let params = {}
    
    // パラメータをパース
    try {
      params = JSON.parse(executionParams.value)
    } catch (error) {
      throw new Error('パラメータのJSON形式が正しくありません')
    }

    // Cloud Functionsエンドポイントを呼び出し
    const response = await fetch(`http://127.0.0.1:5101/umayomi-dev/us-central1/${selectedFunction.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params)
    })

    const endTime = Date.now()
    const duration = endTime - startTime

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    executionResult.value = JSON.stringify(result, null, 2)

    // 実行履歴に追加
    const execution = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      functionName: selectedFunction.value,
      status: 'success',
      duration,
      params,
      result
    }

    // ローカルストレージに保存
    const history = JSON.parse(localStorage.getItem('functionExecutionHistory') || '[]')
    history.unshift(execution)
    if (history.length > 100) history.pop() // 最新100件のみ保持
    localStorage.setItem('functionExecutionHistory', JSON.stringify(history))

    // システム情報を更新
    systemInfo.value.lastExecution = new Date().toLocaleString()
    systemInfo.value.totalExecutions++

    toast.add({
      severity: 'success',
      summary: '実行完了',
      detail: `${selectedFunction.value}の実行が完了しました`,
      life: 3000
    })

  } catch (error: any) {
    console.error('Function実行エラー:', error)
    executionResult.value = `エラー: ${error.message}`
    
    // エラーも履歴に記録
    const execution = {
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      functionName: selectedFunction.value,
      status: 'error',
      duration: 0,
      params: JSON.parse(executionParams.value),
      result: { error: error.message }
    }

    const history = JSON.parse(localStorage.getItem('functionExecutionHistory') || '[]')
    history.unshift(execution)
    if (history.length > 100) history.pop()
    localStorage.setItem('functionExecutionHistory', JSON.stringify(history))

    toast.add({
      severity: 'error',
      summary: '実行エラー',
      detail: error.message,
      life: 5000
    })
  } finally {
    executing.value = false
  }
}

// 実行詳細を表示
const showExecutionDetail = (execution: any) => {
  selectedExecution.value = execution
  showDetailDialog.value = true
}

// ステータスに応じた色を取得
const getStatusSeverity = (status: string) => {
  switch (status) {
    case 'success':
      return 'success'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

// タイムスタンプをフォーマット
const formatTimestamp = (timestamp: string) => {
  return new Date(timestamp).toLocaleString('ja-JP')
}


onMounted(() => {
  refreshHistory()
})
</script>
