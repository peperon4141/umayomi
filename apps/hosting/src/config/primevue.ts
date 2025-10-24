import { definePreset } from '@primeuix/themes'
import Aura from '@primeuix/themes/aura'

export const primeVueConfig = {
  ripple: true,
  locale: {
    firstDayOfWeek: 0,
    dayNames: ['日曜日', '月曜日', '火曜日', '水曜日', '木曜日', '金曜日', '土曜日'],
    dayNamesShort: ['日', '月', '火', '水', '木', '金', '土'],
    dayNamesMin: ['日', '月', '火', '水', '木', '金', '土'],
    monthNames: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    monthNamesShort: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
    today: '今日',
    clear: 'クリア',
    weekHeader: '週'
  },
  pt: {
    datatable: {
      root: {
        class: 'w-full'
      },
      table: {
        class: 'w-full'
      },
      header: {
        class: 'bg-surface-50'
      },
      column: {
        headerCell: {
          class: 'text-sm font-semibold text-surface-700'
        }
      },
      bodyRow: {
        class: 'hover:bg-surface-50 transition-colors duration-200'
      },
      paginator: {
        root: {
          class: 'flex justify-between items-center p-4 bg-surface-0 border-t border-surface-200'
        }
      }
    }
  },
  unstyled: false,
  theme: {
    preset: definePreset(Aura, {
      semantic: {
        primary: {
          50: '{gray.50}',
          100: '{gray.100}',
          200: '{gray.200}',
          300: '{gray.300}',
          400: '{gray.400}',
          500: '{gray.500}',
          600: '{gray.600}',
          700: '{gray.700}',
          800: '{gray.800}',
          900: '{gray.900}',
          950: '{gray.950}'
        },
        colorScheme: {
          light: {
            primary: {
              color: '{gray.800}',
              inverseColor: '#ffffff',
              hoverColor: '{gray.900}',
              activeColor: '{gray.950}'
            },
            highlight: {
              background: '{red.600}',
              focusBackground: '{red.700}',
              color: '#ffffff',
              focusColor: '#ffffff'
            }
          },
          dark: {
            primary: {
              color: '{gray.300}',
              inverseColor: '{gray.950}',
              hoverColor: '{gray.200}',
              activeColor: '{gray.100}'
            },
            highlight: {
              background: 'rgba(239, 68, 68, .16)',
              focusBackground: 'rgba(239, 68, 68, .24)',
              color: 'rgba(255,255,255,.87)',
              focusColor: 'rgba(255,255,255,.87)'
            }
          }
        }
      }
    }),
    options: {
      prefix: 'p',
      darkModeSelector: '.dark',
      cssLayer: {
        name: 'primevue',
        order: 'base, primevue'
      }
    },
  },
}
