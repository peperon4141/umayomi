// ユーザー関連の型定義
export interface UserRole {
  role: 'admin' | 'user'
}

export interface UserProfile {
  uid: string
  email: string
  displayName?: string
  role: UserRole['role']
  createdAt: Date
  lastLoginAt?: Date
}
