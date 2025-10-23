<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <div class="w-64 bg-white shadow-lg flex flex-col">
      <!-- Logo -->
      <div class="p-4 border-b border-gray-200">
        <router-link to="/" class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-red-600 text-white rounded-lg flex items-center justify-center font-bold text-lg">
            馬
          </div>
          <h1 class="text-xl font-bold text-primary">馬読</h1>
        </router-link>
      </div>

      <!-- Navigation Menu -->
      <div class="flex-1 p-4">
        <Menu :model="sidebarMenuItems" class="w-full border-none" />
      </div>

      <!-- User Menu -->
      <div class="p-4 border-t border-gray-200">
        <div class="flex items-center space-x-3">
          <Avatar :label="user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'" size="large" class="font-medium" shape="circle" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-900 truncate">{{ user?.displayName || 'ユーザー' }}</p>
            <p class="text-xs text-gray-500 truncate">{{ user?.email }}</p>
          </div>
          <button @click="(e) => userMenuRef?.toggle(e)" class="p-1 rounded-full hover:bg-gray-100" aria-label="ユーザーメニュー">
            <i class="pi pi-ellipsis-v text-gray-500"></i>
          </button>
          <Menu :model="userMenuItems" popup ref="userMenuRef" />
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <header class="bg-white shadow-sm border-b border-gray-200 px-6 py-2">
        <Breadcrumb />
      </header>

      <!-- Content -->
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>

    <!-- Profile Dialog -->
    <ProfileDialog v-model:visible="showProfileDialog" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import ProfileDialog from '@/components/ProfileDialog.vue'
import Breadcrumb from '@/components/Breadcrumb.vue'

const router = useRouter()
const route = useRoute()
const { user, isAdmin, signOut } = useAuth()
const userMenuRef = ref()
const showProfileDialog = ref(false)

// サイドバーメニュー
const sidebarMenuItems = computed(() => [
  {
    label: 'レース一覧',
    icon: 'pi pi-list',
    command: () => router.push('/races/year/2024'),
    class: isActiveRoute('/races') ? 'bg-primary-50 text-primary' : ''
  },
  {
    label: 'ダッシュボード',
    icon: 'pi pi-chart-bar',
    command: () => router.push('/dashboard'),
    class: isActiveRoute('/dashboard') ? 'bg-primary-50 text-primary' : ''
  },
  ...(isAdmin.value ? [{
    label: '管理画面',
    icon: 'pi pi-cog',
    command: () => router.push('/admin'),
    class: isActiveRoute('/admin') ? 'bg-primary-50 text-primary' : ''
  }] : [])
])

// ユーザーメニュー
const userMenuItems = computed(() => [
  { label: 'プロフィール', icon: 'pi pi-user', command: () => { showProfileDialog.value = true } },
  { separator: true },
  { label: 'ログアウト', icon: 'pi pi-sign-out', command: () => { handleLogout() }, ariaLabel: 'ログアウト' }
])

// 現在のルートがアクティブかチェック
const isActiveRoute = (path: string) => {
  return route.path.startsWith(path)
}

const handleLogout = async () => {
  try {
    await signOut()
    router.push('/')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}
</script>
