<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Fixed Header -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-white shadow-sm border-b-2 border-gray-300" style="height: 4em;">
      <div class="flex items-center justify-between px-4 h-full">
        <!-- Left Side -->
        <div class="flex items-center space-x-4">
          <!-- Mobile Menu Button -->
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="lg:hidden p-2 rounded-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="メニューを開く"
          >
            <i class="pi pi-bars text-gray-600"></i>
          </button>

          <!-- Logo -->
          <router-link to="/" class="flex items-center space-x-2">
            <div class="w-8 h-8 bg-red-600 text-white rounded-lg flex items-center justify-center font-bold text-lg">
              馬
            </div>
            <h1 class="text-xl font-bold text-primary">馬読</h1>
          </router-link>
        </div>

        <!-- Right Side -->
        <div class="flex items-center">
          <!-- User Menu -->
          <div class="flex items-center">
            <button 
              @click="(e) => userMenuRef?.toggle(e)" 
              class="p-2 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500" 
              aria-label="ユーザーメニュー"
            >
              <Avatar 
                :label="user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'" 
                size="normal" 
                class="font-medium" 
                shape="circle" 
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
          'w-48 bg-white shadow-lg flex flex-col transition-transform duration-300 ease-in-out',
          'fixed lg:fixed inset-y-0 left-0 z-50',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        ]"
        style="top: 4em; height: calc(100vh - 4em);"
      >
        <!-- Navigation Menu -->
        <div class="flex-1 p-3 overflow-y-auto">
          <Menu :model="sidebarMenuItems" class="w-full border-none sidebar-menu" />
        </div>
      </div>

      <!-- Content -->
      <main class="flex-1 lg:ml-48">
        <!-- Breadcrumb -->
        <div class="bg-white border-b border-gray-200 px-4 flex items-center overflow-hidden" style="height: 3em;">
          <div class="w-full" style="white-space: nowrap; overflow-x: auto;">
            <Breadcrumb />
          </div>
        </div>
        
        <!-- Page Content -->
        <div class="p-3 sm:p-4">
          <slot />
        </div>
      </main>
    </div>

    <!-- Mobile Overlay -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
      @click="sidebarOpen = false"
    ></div>


    <!-- Profile Dialog -->
    <ProfileDialog v-model:visible="showProfileDialog" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useNavigation } from '@/composables/useNavigation'
import ProfileDialog from '@/components/ProfileDialog.vue'
import Breadcrumb from '@/components/Breadcrumb.vue'
import { RouteName, getCurrentYear } from '@/router/routeCalculator'

const router = useRouter()
const route = useRoute()
const { user, isAdmin, signOut } = useAuth()
const { navigateTo } = useNavigation()
const userMenuRef = ref()
const showProfileDialog = ref(false)
const sidebarOpen = ref(false)


// サイドバーメニュー
const sidebarMenuItems = computed(() => [
  {
    label: 'レース一覧',
    icon: 'pi pi-list',
    command: () => {
      navigateTo(RouteName.RACE_LIST_IN_YEAR, { year: getCurrentYear() })
      sidebarOpen.value = false
    },
    class: isActiveRoute('/races') ? 'bg-primary-50 text-primary' : ''
  }
])

  // ユーザーメニュー
  const userMenuItems = computed(() => [
    { 
      label: 'プロフィール', 
      icon: 'pi pi-user', 
      command: () => { 
        showProfileDialog.value = true
        sidebarOpen.value = false // メニューを閉じる
      } 
    },
    ...(isAdmin.value ? [{ 
      label: '管理者画面', 
      icon: 'pi pi-shield', 
      command: () => { 
        router.push('/admin')
        sidebarOpen.value = false
      } 
    }] : []),
    { separator: true },
    { 
      label: 'ログアウト', 
      icon: 'pi pi-sign-out', 
      command: () => { 
        handleLogout()
        sidebarOpen.value = false
      }, 
      ariaLabel: 'ログアウト' 
    }
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
