<template>
  <div class="space-y-6">
    <div class="mb-8">
      <h2 class="text-3xl font-bold text-surface-900 mb-2">モデル管理</h2>
      <p class="text-surface-600">学習済みモデルのアップロードと一覧</p>
    </div>

    <Card>
      <template #header>
        <div class="p-6 border-b border-surface-border">
          <h3 class="text-xl font-bold text-surface-900">モデルのアップロード</h3>
          <p class="text-surface-600 mt-1">Storageへアップロードし、Firestore(models)にメタデータを登録します</p>
        </div>
      </template>
      <template #content>
        <div class="p-6 space-y-4">
          <Message v-if="uploadError" severity="error" :closable="false">{{ uploadError }}</Message>
          <Message v-if="uploadSuccess" severity="success" :closable="false">{{ uploadSuccess }}</Message>

          <div class="flex items-center gap-3">
            <FileUpload
              mode="basic"
              name="model"
              accept=".txt"
              :maxFileSize="10 * 1024 * 1024"
              chooseLabel="ファイルを選択"
              :disabled="uploading"
              customUpload
              @select="onFileSelect"
            />
            <Chip v-if="selectedFileName" :label="selectedFileName" severity="info" />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-surface-900 mb-2">モデル名（必須）</label>
              <InputText v-model="modelName" class="w-full" placeholder="rank_model_YYYYMMDDHHmm_v1" :disabled="uploading" />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-900 mb-2">Storageパス（必須）</label>
              <InputText v-model="storagePath" class="w-full" placeholder="models/xxx.txt" :disabled="uploading" />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-900 mb-2">バージョン（任意）</label>
              <InputText v-model="version" class="w-full" placeholder="1.0" :disabled="uploading" />
            </div>
            <div>
              <label class="block text-sm font-medium text-surface-900 mb-2">学習日（任意）</label>
              <Calendar v-model="trainingDate" class="w-full" dateFormat="yy-mm-dd" showIcon :disabled="uploading" />
            </div>
            <div class="md:col-span-2">
              <label class="block text-sm font-medium text-surface-900 mb-2">説明（任意）</label>
              <Textarea v-model="description" class="w-full" rows="3" :disabled="uploading" />
            </div>
          </div>

          <div class="flex justify-end">
            <Button
              label="アップロード"
              icon="pi pi-upload"
              severity="info"
              :loading="uploading"
              :disabled="!canUpload"
              @click="uploadModel"
            />
          </div>
        </div>
      </template>
    </Card>

    <Card>
      <template #header>
        <div class="p-6 border-b border-surface-border">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-xl font-bold text-surface-900">モデル一覧</h3>
              <p class="text-surface-600 mt-1">Firestore(models)の最新順</p>
            </div>
            <Button icon="pi pi-refresh" severity="secondary" text @click="refreshModels" :disabled="modelsLoading" v-tooltip.top="'更新'" />
          </div>
        </div>
      </template>
      <template #content>
        <div class="p-6">
          <div v-if="modelsLoading" class="text-center py-8">
            <ProgressSpinner />
            <p class="mt-4 text-surface-600">読み込み中...</p>
          </div>

          <Message v-else-if="modelsError" severity="error" :closable="false">{{ modelsError }}</Message>

          <div v-else>
            <DataTable :value="models" dataKey="model_name" :paginator="models.length > 20" :rows="20" stripedRows>
              <Column field="model_name" header="モデル名" />
              <Column field="version" header="version" />
              <Column field="training_date" header="学習日" />
              <Column field="storage_path" header="storage_path" />
              <Column header="有効">
                <template #body="{ data }">
                  <InputSwitch
                    :modelValue="data.is_active !== false"
                    @update:modelValue="(value: boolean) => toggleModelActive(data.model_name, value)"
                    :disabled="updatingModel === data.model_name"
                  />
                </template>
              </Column>
              <Column header="作成日時">
                <template #body="{ data }">{{ formatDate(data.created_at) }}</template>
              </Column>
            </DataTable>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { collection, doc, getDocs, limit, orderBy, query, updateDoc } from 'firebase/firestore'
import { auth, db } from '@/config/firebase'
import { getFunctionUrl } from '@/utils/functionUrl'

type ModelDoc = {
  model_name: string
  storage_path: string
  storage_url?: string
  version?: string
  description?: string
  training_date?: string
  is_active?: boolean
  created_at?: any
}

const uploading = ref(false)
const uploadError = ref<string | null>(null)
const uploadSuccess = ref<string | null>(null)

const selectedFile = ref<File | null>(null)
const selectedFileName = computed(() => selectedFile.value?.name ?? '')

const modelName = ref('')
const storagePath = ref('')
const version = ref('')
const description = ref('')
const trainingDate = ref<Date | null>(null)

const modelsLoading = ref(false)
const modelsError = ref<string | null>(null)
const models = ref<ModelDoc[]>([])
const updatingModel = ref<string | null>(null)

const canUpload = computed(() => {
  if (uploading.value) return false
  if (!selectedFile.value) return false
  if (modelName.value.trim().length === 0) return false
  if (storagePath.value.trim().length === 0) return false
  return true
})

const onFileSelect = async (event: any) => {
  uploadError.value = null
  uploadSuccess.value = null
  const file = event?.files?.[0] as File | undefined
  if (!file) return
  selectedFile.value = file

  // ファイル名から自動抽出
  const fileNameWithoutExt = file.name.replace(/\.txt$/i, '')
  if (modelName.value.trim().length === 0) modelName.value = fileNameWithoutExt
  if (storagePath.value.trim().length === 0) storagePath.value = `models/${file.name}`

  // ファイル名からタイムスタンプとバージョンを抽出
  // 例: rank_model_202512180040_v1 → 2025-12-18, v1
  const timestampMatch = fileNameWithoutExt.match(/(\d{12})/)
  if (timestampMatch && !trainingDate.value) {
    const ts = timestampMatch[1]
    const year = parseInt(ts.slice(0, 4), 10)
    const month = parseInt(ts.slice(4, 6), 10) - 1
    const day = parseInt(ts.slice(6, 8), 10)
    if (year >= 2020 && year <= 2100 && month >= 0 && month <= 11 && day >= 1 && day <= 31) {
      trainingDate.value = new Date(year, month, day)
    }
  }

  const versionMatch = fileNameWithoutExt.match(/_v(\d+)$/)
  if (versionMatch && version.value.trim().length === 0) {
    version.value = versionMatch[1]
  }

  // ファイル内容からメタ情報を抽出
  try {
    const text = await file.text()
    const lines = text.split('\n')
    const metaInfo: string[] = []

    // feature_names から特徴量数を取得
    const featureNamesLine = lines.find((line) => line.startsWith('feature_names='))
    if (featureNamesLine) {
      const features = featureNamesLine.replace('feature_names=', '').trim().split(/\s+/)
      const featureCount = features.filter((f) => f.length > 0).length
      if (featureCount > 0) metaInfo.push(`${featureCount}特徴量`)
    }

    // objective から目的関数を取得
    const objectiveLine = lines.find((line) => line.startsWith('objective='))
    if (objectiveLine) {
      const objective = objectiveLine.replace('objective=', '').trim()
      if (objective) metaInfo.push(`objective: ${objective}`)
    }

    // num_class からクラス数を取得
    const numClassLine = lines.find((line) => line.startsWith('num_class='))
    if (numClassLine) {
      const numClass = numClassLine.replace('num_class=', '').trim()
      if (numClass) metaInfo.push(`${numClass}クラス`)
    }

    // max_feature_idx から最大特徴量インデックスを取得
    const maxFeatureIdxLine = lines.find((line) => line.startsWith('max_feature_idx='))
    if (maxFeatureIdxLine) {
      const maxFeatureIdx = maxFeatureIdxLine.replace('max_feature_idx=', '').trim()
      if (maxFeatureIdx) metaInfo.push(`max_feature_idx: ${maxFeatureIdx}`)
    }

    if (metaInfo.length > 0 && description.value.trim().length === 0) {
      description.value = metaInfo.join(', ')
    }
  } catch (e) {
    // ファイル読み込みエラーは無視（手動入力にフォールバック）
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunkSize = 0x8000
  for (let i = 0; i < bytes.length; i += chunkSize) binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize))
  return btoa(binary)
}

function formatDate(value: any): string {
  if (!value) return ''
  if (typeof value?.toDate === 'function') return value.toDate().toLocaleString('ja-JP')
  if (value?.seconds) return new Date(value.seconds * 1000).toLocaleString('ja-JP')
  if (typeof value === 'string') return value
  return ''
}

function toYmd(date: Date): string {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const uploadModel = async () => {
  uploadError.value = null
  uploadSuccess.value = null

  if (!selectedFile.value) {
    uploadError.value = 'ファイルを選択してください'
    return
  }
  if (modelName.value.trim().length === 0) {
    uploadError.value = 'モデル名は必須です'
    return
  }
  if (storagePath.value.trim().length === 0) {
    uploadError.value = 'Storageパスは必須です'
    return
  }

  const user = auth.currentUser
  if (!user) {
    uploadError.value = 'ログインが必要です'
    return
  }

  uploading.value = true
  try {
    const token = await user.getIdToken()
    const buffer = await selectedFile.value.arrayBuffer()
    const contentBase64 = arrayBufferToBase64(buffer)
    const body = {
      fileName: selectedFile.value.name,
      contentBase64,
      modelName: modelName.value.trim(),
      storagePath: storagePath.value.trim(),
      version: version.value.trim().length > 0 ? version.value.trim() : undefined,
      description: description.value.trim().length > 0 ? description.value.trim() : undefined,
      trainingDate: trainingDate.value ? toYmd(trainingDate.value) : undefined
    }

    const res = await fetch(getFunctionUrl('uploadModel'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(body)
    })

    const json = await res.json().catch(() => ({}))
    if (!res.ok || !json?.success) throw new Error(json?.error || `HTTP error! status: ${res.status}`)

    uploadSuccess.value = `アップロード完了: ${json.storagePath}`
    await refreshModels()
  } catch (e: unknown) {
    uploadError.value = e instanceof Error ? e.message : String(e)
  } finally {
    uploading.value = false
  }
}

const refreshModels = async () => {
  modelsLoading.value = true
  modelsError.value = null
  try {
    const q = query(collection(db, 'models'), orderBy('created_at', 'desc'), limit(50))
    const snap = await getDocs(q)
    models.value = snap.docs.map((d) => ({ model_name: d.id, ...(d.data() as any) }))
  } catch (e: unknown) {
    modelsError.value = e instanceof Error ? e.message : String(e)
  } finally {
    modelsLoading.value = false
  }
}

const toggleModelActive = async (modelName: string, isActive: boolean) => {
  updatingModel.value = modelName
  try {
    const modelRef = doc(db, 'models', modelName)
    await updateDoc(modelRef, {
      is_active: isActive,
      updated_at: new Date()
    })
    await refreshModels()
  } catch (e: unknown) {
    const errorMessage = e instanceof Error ? e.message : String(e)
    modelsError.value = `モデルの有効/無効の更新に失敗しました: ${errorMessage}`
  } finally {
    updatingModel.value = null
  }
}

onMounted(async () => {
  await refreshModels()
})
</script>


