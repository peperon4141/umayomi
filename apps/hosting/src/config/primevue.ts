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
  unstyled: false,
  theme: {
    preset: definePreset(Aura, {
      semantic: {
        primary: {
          50: '{red.50}',
          100: '{red.100}',
          200: '{red.200}',
          300: '{red.300}',
          400: '{red.400}',
          500: '{red.500}',
          600: '{red.600}',
          700: '{red.700}',
          800: '{red.800}',
          900: '{red.900}',
          950: '{red.950}'
        },
        colorScheme: {
          light: {
            primary: {
              color: '{red.600}',
              inverseColor: '#ffffff',
              hoverColor: '{red.700}',
              activeColor: '{red.800}'
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
              color: '{red.400}',
              inverseColor: '{red.950}',
              hoverColor: '{red.300}',
              activeColor: '{red.200}'
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
