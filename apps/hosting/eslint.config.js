import js from '@eslint/js'
import typescript from '@typescript-eslint/eslint-plugin'
import typescriptParser from '@typescript-eslint/parser'
import vue from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'

export default [
  {
    ignores: ['dist/**', 'node_modules/**', 'components.d.ts', '**/*.d.ts'],
  },
  {
    files: ['src/**/*.{js,ts,vue}'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: typescriptParser,
        ecmaVersion: 'latest',
        sourceType: 'module'
      },
      globals: {
        document: 'readonly',
        window: 'readonly',
        console: 'readonly',
        location: 'readonly',
        history: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        Element: 'readonly',
        HTMLElement: 'readonly',
        SVGElement: 'readonly',
        MathMLElement: 'readonly',
        ShadowRoot: 'readonly',
        getComputedStyle: 'readonly',
        MutationObserver: 'readonly'
      }
    },
    plugins: {
      '@typescript-eslint': typescript,
      vue
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'warn',
      'vue/multi-word-component-names': 'off'
    }
  }
]
