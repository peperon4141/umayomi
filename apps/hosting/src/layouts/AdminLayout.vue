<template>
  <div class="min-h-screen bg-surface-100">
    <!-- Fixed Header -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-surface-0 shadow-sm border-b border-surface-border" style="height: 4em;">
      <div class="flex items-center justify-between px-4 h-full">
        <!-- Left Side -->
        <div class="flex items-center space-x-4">
          <!-- Mobile Menu Button -->
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="lg:hidden p-2 rounded-md hover:bg-surface-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="メニューを開く"
          >
            <i class="pi pi-bars text-surface-600"></i>
          </button>

          <!-- Logo -->
          <div class="flex items-center space-x-2">
            <h1 class="text-xl font-bold text-surface-900">管理ダッシュボード</h1>
          </div>
        </div>

        <!-- Right Side -->
        <div class="flex items-center space-x-2">
          <Button
            label="メインアプリに戻る"
            icon="pi pi-arrow-left"
            severity="secondary"
            size="small"
            @click="goToMainApp"
          />
          
          <!-- User Menu -->
          <div class="flex items-center">
            <button 
              @click="(e) => userMenuRef?.toggle(e)" 
              class="p-2 rounded-full hover:bg-surface-100 focus:outline-none focus:ring-2 focus:ring-primary-500" 
              aria-label="ユーザーメニュー"
            >
              <Avatar 
                :label="user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'A'" 
                size="normal" 
                class="font-medium" 
                shape="circle"
                style="background-color: var(--p-purple-500); color: white;"
              />
            </button>

            <Menu :model="userMenuItems" popup ref="userMenuRef" />
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="flex-1 min-w-0 flex" style="padding-top: 4em;">
      <!-- Sidebar -->
      <div
        :class="[
          'w-64 bg-surface-0 shadow-lg flex flex-col transition-transform duration-300 ease-in-out',
          'fixed lg:fixed inset-y-0 left-0 z-40',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        ]"
        style="top: 4em; height: calc(100vh - 4em);"
      >
        
        <!-- Navigation Menu -->
        <div class="flex-1 p-3 overflow-y-auto">
          <Menu :model="menuItems" class="w-full border-none sidebar-menu" />
        </div>
      </div>

      <!-- Content -->
      <main class="flex-1 lg:ml-64">
        <!-- Page Content -->
        <div class="p-3 sm:p-4">
          <slot />
        </div>
      </main>
    </div>

    <!-- Mobile Overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
      @click="sidebarOpen = false"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import Button from 'primevue/button'
import Avatar from 'primevue/avatar'
import Menu from 'primevue/menu'

const router = useRouter()
const { user, signOut } = useAuth()
const userMenuRef = ref()
const sidebarOpen = ref(false)

// サイドバーのメニュー項目
const menuItems = ref([
  {
    label: 'Overview',
    icon: 'pi pi-home',
    command: () => {
      emit('navigate', 'overview')
      sidebarOpen.value = false
    }
  },
  {
    label: 'スクレイピング',
    icon: 'pi pi-download',
    command: () => {
      emit('navigate', 'scraping')
      sidebarOpen.value = false
    }
  }
])

// ユーザーメニュー
const userMenuItems = ref([
  { 
    label: 'プロフィール', 
    icon: 'pi pi-user', 
    command: () => { 
      // プロフィールダイアログを表示（将来実装）
      console.log('プロフィールを表示')
    } 
  },
  { 
    label: '設定', 
    icon: 'pi pi-cog', 
    command: () => { 
      // 設定ページへの遷移（将来実装）
      console.log('設定ページへ遷移')
    } 
  },
  { separator: true },
  { 
    label: 'ログアウト', 
    icon: 'pi pi-sign-out', 
    command: () => { 
      handleLogout()
    }, 
    ariaLabel: 'ログアウト' 
  }
])

// Emits
const emit = defineEmits<{
  navigate: [page: string]
}>()

const goToMainApp = () => {
  router.push('/race-list')
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

<style scoped>
.sidebar-menu :deep(.p-menuitem) {
  margin-bottom: 0.5rem;
}

.sidebar-menu :deep(.p-menuitem:last-child) {
  margin-bottom: 0;
}

.sidebar-menu :deep(.p-menuitem-link) {
  padding: 0.5rem 0.75rem;
  border-radius: 0.5rem;
  transition: all 0.2s ease;
}

.sidebar-menu :deep(.p-menuitem-link:hover) {
  background-color: var(--p-surface-100);
}

.sidebar-menu :deep(.p-menuitem-link:focus) {
  outline: none;
  box-shadow: 0 0 0 2px var(--p-primary-100);
}
</style>
