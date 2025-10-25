<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-900 mb-4">月別レース一覧</h1>
        <p class="text-gray-600 mb-8">このページは現在開発中です</p>
        <Button
          label="ダッシュボードに戻る"
          icon="pi pi-arrow-left"
          @click="goToDashboard"
        />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import Button from 'primevue/button'

const router = useRouter()

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>