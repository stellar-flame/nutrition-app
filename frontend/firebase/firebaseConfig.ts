import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getApps } from 'firebase/app';

// Firebase configuration - hardcoded for reliability
const firebaseConfig = {
  apiKey: "AIzaSyCqDfcZb-nnNXucNBqrPDVTL58RfnD3hV8",
  authDomain: "nutrition-app-2efea.firebaseapp.com",
  projectId: "nutrition-app-2efea",
  storageBucket: "nutrition-app-2efea.firebasestorage.app",
  messagingSenderId: "17932674962",
  appId: "1:17932674962:web:a3dfd5384dd0d4872e034b"
};


// Debug: Log Firebase config in production
console.log('🔥 Firebase Config:', {
  apiKey: firebaseConfig.apiKey ? 'SET' : 'MISSING',
  authDomain: firebaseConfig.authDomain ? 'SET' : 'MISSING',
  projectId: firebaseConfig.projectId ? 'SET' : 'MISSING',
  storageBucket: firebaseConfig.storageBucket ? 'SET' : 'MISSING',
  messagingSenderId: firebaseConfig.messagingSenderId ? 'SET' : 'MISSING',
  appId: firebaseConfig.appId ? 'SET' : 'MISSING',
});

// Validate configuration
if (!firebaseConfig.apiKey || !firebaseConfig.authDomain || !firebaseConfig.projectId) {
  console.error('❌ Firebase config is incomplete!', firebaseConfig);
  throw new Error('Firebase configuration is incomplete');
}

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
export const auth = getAuth(app);