import js from '@eslint/js'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.ts', 'tests/**/*.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: './tsconfig.json'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint
    },
    rules: {
      'no-console': 'warn',
      'prefer-const': 'error',
      'no-var': 'error',
      'no-undef': 'off', // TypeScriptが型チェックを行うため
      '@typescript-eslint/no-unused-vars': 'error'
    }
  },
  {
    files: ['scripts/**/*.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: './tsconfig.json'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint
    },
    rules: {
      'no-console': 'off', // スクリプトファイルではconsole.logを許可
      'prefer-const': 'error',
      'no-var': 'error',
      'no-undef': 'off',
      '@typescript-eslint/no-unused-vars': 'error'
    }
  },
  {
    files: ['lib/**/*.js'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'commonjs',
      globals: {
        'exports': 'readonly',
        'require': 'readonly',
        'module': 'readonly',
        '__dirname': 'readonly',
        '__filename': 'readonly',
        'process': 'readonly',
        'global': 'readonly'
      }
    },
    rules: {
      'no-console': 'warn'
    }
  }
]
