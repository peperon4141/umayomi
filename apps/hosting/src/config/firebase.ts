import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  connectAuthEmulator,
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  User,
  createUserWithEmailAndPassword,
  GoogleAuthProvider,
  signInWithPopup
} from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';

// Firebase設定（環境変数を使用）
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID
};

// デバッグ用: Firebase設定をログ出力
console.log('🔍 Firebase設定:', firebaseConfig);

// Firebaseアプリを初期化
const app = initializeApp(firebaseConfig);

// AuthとFirestoreのインスタンスを取得
export const auth = getAuth(app);
export const db = getFirestore(app);

// エミュレーター使用フラグでエミュレーターに接続
if (import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true' || import.meta.env.DEV) {
  try {
    // Authエミュレーターに接続（firebase.jsonの設定を使用）
    connectAuthEmulator(auth, 'http://127.0.0.1:9199', { disableWarnings: true });
    console.log('✅ Authエミュレーターに接続: 127.0.0.1:9199');

    // Firestoreエミュレーターに接続（firebase.jsonの設定を使用）
    connectFirestoreEmulator(db, '127.0.0.1', 8180);
    console.log('✅ Firestoreエミュレーターに接続: 127.0.0.1:8180');
  } catch (error) {
    console.warn('⚠️ エミュレーター接続エラー（既に接続済みの可能性）:', error);
  }
}

// 認証ユーティリティ関数
export const loginWithEmail = async (email: string, password: string) => {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return { user: userCredential.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

export const registerWithEmail = async (email: string, password: string) => {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    return { user: userCredential.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

export const logout = async () => {
  try {
    await signOut(auth);
    return { error: null };
  } catch (error: any) {
    return { error: error.message };
  }
};

export const getCurrentUser = (): User | null => {
  return auth.currentUser;
};

export const onAuthChange = (callback: (user: User | null) => void) => {
  return onAuthStateChanged(auth, callback);
};

// Google認証
export const loginWithGoogle = async () => {
  try {
    const provider = new GoogleAuthProvider();
    const userCredential = await signInWithPopup(auth, provider);
    return { user: userCredential.user, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

export default app;
