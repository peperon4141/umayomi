/**
 * ESLint共通ルール設定
 * 全プロジェクトで統一されたルールを定義
 */

export const rules = {
  // 基本ルール（最小限）
  'no-console': 'warn', // 本番コードでのconsole.logを警告
  'no-debugger': 'warn', // 本番コードでのdebuggerを警告
  'no-undef': 'error', // 未定義変数はエラー
  
  // 必須のコードスタイル
  'prefer-const': 'error', // letよりconstを推奨（不変性の推奨）
  'no-var': 'error', // varの使用を禁止（let/constを推奨）
  'semi': ['error', 'never'], // セミコロンなし
  'quotes': ['error', 'single'], // シングルクォート使用
  'no-multiple-empty-lines': ['error', { max: 1, maxEOF: 0 }], // 複数空行を禁止（最大1行、ファイル末尾は0行）
  
  // TypeScript固有ルール
  'no-unused-vars': 'off', // TypeScript版を使用するため無効化
  '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }], // 未使用変数を警告（_で始まる引数は除外）
  '@typescript-eslint/no-explicit-any': 'warn', // anyの使用を警告（型安全性の推奨）
  '@typescript-eslint/consistent-type-imports': 'error' // 型インポートの統一（import typeの推奨）
}
