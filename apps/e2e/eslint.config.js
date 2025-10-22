import js from '@eslint/js'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import { rules } from '../eslint-rules.js'

export default [
  js.configs.recommended,
  {
    files: ['**/*.{js,ts}'],
    ignores: ['**/node_modules/**', '**/dist/**', '**/test-results/**', '**/playwright-report/**'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module'
      },
      globals: {
        process: 'readonly',
        module: 'readonly',
        console: 'readonly',
        test: 'readonly',
        expect: 'readonly',
        describe: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        beforeAll: 'readonly',
        afterAll: 'readonly'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint
    },
    rules: {
      ...rules,
      'no-undef': 'off' // Playwrightのグローバル変数（test, expect, describe等）を許可
    }
  }
]
