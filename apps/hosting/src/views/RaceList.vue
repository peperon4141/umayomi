<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-900 mb-2">レース一覧</h1>
        <p class="text-gray-600 mb-4">このページは現在開発中です</p>
        <Button
          label="レース一覧に戻る"
          icon="pi pi-arrow-left"
          @click="goToRaceList"
        />
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

const goToRaceList = () => {
  navigateTo(RouteName.RACES)
}
</script>