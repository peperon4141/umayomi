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
  signInWithRedirect,
  getRedirectResult
} from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
import { getFunctions, connectFunctionsEmulator } from 'firebase/functions';

// Firebase設定（エミュレーター用の設定）
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
export const functions = getFunctions(app);

// エミュレーター使用フラグでエミュレーターに接続
if (import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true' || import.meta.env.DEV) {
  try {
    // Authエミュレーターに接続（firebase.jsonの設定を使用）
    connectAuthEmulator(auth, 'http://127.0.0.1:9199', { disableWarnings: true });
    console.log('✅ Authエミュレーターに接続: 127.0.0.1:9199');

    // Firestoreエミュレーターに接続（firebase.jsonの設定を使用）
    connectFirestoreEmulator(db, '127.0.0.1', 8180);
    console.log('✅ Firestoreエミュレーターに接続: 127.0.0.1:8180');

    // Functionsエミュレーターに接続
    connectFunctionsEmulator(functions, '127.0.0.1', 5101);
    console.log('✅ Functionsエミュレーターに接続: 127.0.0.1:5101');
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

// Google認証（リダイレクト方式）
export const loginWithGoogle = async () => {
  try {
    const provider = new GoogleAuthProvider();
    await signInWithRedirect(auth, provider);
    return { user: null, error: null }; // リダイレクトが発生するため、ここではuserはnull
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

// リダイレクト後の結果を取得
export const getGoogleRedirectResult = async () => {
  try {
    const result = await getRedirectResult(auth);
    if (result) {
      return { user: result.user, error: null };
    }
    return { user: null, error: null };
  } catch (error: any) {
    return { user: null, error: error.message };
  }
};

// onAuthStateChangedをエクスポート
export { onAuthStateChanged };

export default app;
