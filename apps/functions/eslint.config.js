import js from '@eslint/js'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import oneLinePlugin from '../eslint-rules/one-line.js'

export default [
  js.configs.recommended,
  {
    ignores: [
      'lib/**',
      'node_modules/**',
      '**/*.js.map',
      '**/*.d.ts'
    ]
  },
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: './tsconfig.json'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint,
      'one-line': oneLinePlugin
    },
    rules: {
      'no-console': 'warn',
      'prefer-const': 'error',
      'no-var': 'error',
      'no-undef': 'off', // TypeScriptが型チェックを行うため
      '@typescript-eslint/no-unused-vars': 'error',
      // 1行しか含まないアロー演算子、if文は1行で実装
      'arrow-body-style': ['error', 'as-needed'],
      'curly': ['error', 'multi'],
      // カスタムルール: 1行しか含まないif文、アロー関数、case文は1行で実装
      'one-line/single-line-if': 'error',
      'one-line/single-line-arrow': 'error',
      'one-line/single-line-case': 'error'
    }
  },
  {
    files: ['tests/**/*.ts'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: './tsconfig.test.json'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint,
      'one-line': oneLinePlugin
    },
    rules: {
      'no-console': 'warn',
      'prefer-const': 'error',
      'no-var': 'error',
      'no-undef': 'off', // TypeScriptが型チェックを行うため
      '@typescript-eslint/no-unused-vars': 'error',
      // 1行しか含まないアロー演算子、if文は1行で実装
      'arrow-body-style': ['error', 'as-needed'],
      'curly': ['error', 'multi'],
      // カスタムルール: 1行しか含まないif文、アロー関数、case文は1行で実装
      'one-line/single-line-if': 'error',
      'one-line/single-line-arrow': 'error',
      'one-line/single-line-case': 'error'
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
      '@typescript-eslint': tseslint,
      'one-line': oneLinePlugin
    },
    rules: {
      'no-console': 'off', // スクリプトファイルではconsole.logを許可
      'prefer-const': 'error',
      'no-var': 'error',
      'no-undef': 'off',
      '@typescript-eslint/no-unused-vars': 'error',
      // 1行しか含まないアロー演算子、if文は1行で実装
      'arrow-body-style': ['error', 'as-needed'],
      'curly': ['error', 'multi'],
      // カスタムルール: 1行しか含まないif文、アロー関数、case文は1行で実装
      'one-line/single-line-if': 'error',
      'one-line/single-line-arrow': 'error',
      'one-line/single-line-case': 'error'
    }
  },
  {
    files: ['scripts/**/*.js', 'scripts/**/*.ts'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: 'module',
        project: false // scriptsディレクトリは型チェックをスキップ
      },
      globals: {
        'require': 'readonly',
        '__dirname': 'readonly',
        '__filename': 'readonly',
        'process': 'readonly',
        'module': 'readonly',
        'exports': 'readonly',
        'global': 'readonly'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint
    },
    rules: {
      'no-console': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
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
