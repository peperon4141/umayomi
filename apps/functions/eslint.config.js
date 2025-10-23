import js from '@eslint/js'

export default [
  js.configs.recommended,
  {
    files: ['src/**/*.ts'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module'
    },
    rules: {
      'no-console': 'warn',
      'prefer-const': 'error',
      'no-var': 'error'
    }
  }
]
