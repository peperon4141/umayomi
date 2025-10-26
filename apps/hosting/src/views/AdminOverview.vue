<template>
  <div class="space-y-6">
    <!-- ページヘッダー -->
    <div class="mb-8">
      <h2 class="text-3xl font-bold text-surface-900 mb-2">システム概要</h2>
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

      <!-- システム情報カード -->
      <Card class="bg-surface-50">
        <template #content>
          <div class="p-6">
            <h4 class="font-semibold text-surface-900 mb-4">システム情報</h4>
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
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRace } from '@/composables/useRace'
import { getCurrentYear, getCurrentMonth } from '@/router/routeCalculator'
import Card from 'primevue/card'
import Badge from 'primevue/badge'

const { races, fetchOctoberRaces } = useRace()

// 統計データ
const totalRaces = ref(0)
const monthlyRaces = ref(0)
const activeUsers = ref(1)
const lastUpdate = ref(`${getCurrentYear()}年${getCurrentMonth()}月15日`)

onMounted(async () => {
  // Firestoreからレースデータを取得
  await fetchOctoberRaces()
  
  // 統計データの計算
  totalRaces.value = races.value.length
  monthlyRaces.value = races.value.length
  activeUsers.value = 1
})
</script>
