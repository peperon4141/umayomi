<template>
  <AppLayout>
    <div class="min-h-screen flex items-center justify-center bg-surface-50">
      <div class="max-w-md w-full text-center">
        <div class="mb-8">
          <h1 class="text-9xl font-bold text-surface-300 mb-4">404</h1>
          <h2 class="text-2xl font-semibold text-surface-700 mb-4">ページが見つかりません</h2>
          <p class="text-surface-600 mb-8">
            お探しのページは存在しないか、移動された可能性があります。
          </p>
        </div>
        
        <div class="space-y-4">
          <Button 
            label="ホームに戻る" 
            icon="pi pi-home" 
            @click="goHome"
            class="w-full"
            severity="primary"
          />
          <Button 
            label="前のページに戻る" 
            icon="pi pi-arrow-left" 
            @click="goBack"
            class="w-full"
            severity="secondary"
            outlined
          />
        </div>
        
        <div class="mt-8 text-sm text-surface-500">
          <p>問題が解決しない場合は、管理者にお問い合わせください。</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { useNavigation } from '@/composables/useNavigation'
import AppLayout from '@/layouts/AppLayout.vue'
import Button from 'primevue/button'
import { RouteName } from '@/router/routeCalculator'

const { navigateTo } = useNavigation()

const goHome = () => {
  navigateTo(RouteName.HOME)
}

const goBack = () => {
  window.history.back()
}
</script>
