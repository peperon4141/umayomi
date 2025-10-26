<template>
  <AdminLayout @navigate="handleNavigate">
    <!-- Overview ページ -->
    <AdminOverview v-if="currentPage === 'overview'" />
    
    <!-- スクレイピング ページ -->
    <AdminScraping v-else-if="currentPage === 'scraping'" />
    
    <!-- デフォルト（Overview） -->
    <AdminOverview v-else />
  </AdminLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AdminLayout from '@/layouts/AdminLayout.vue'
import AdminOverview from '@/views/AdminOverview.vue'
import AdminScraping from '@/views/AdminScraping.vue'

const currentPage = ref('overview')

const handleNavigate = (page: string) => {
  currentPage.value = page
}
</script>