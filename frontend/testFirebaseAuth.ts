import { initializeApp } from 'firebase/app';
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from 'firebase/auth';

// Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyCHnwqk2wB2GC5uiz4myKbshKAfvkYZqSE",
  authDomain: "health-app-ed269.firebaseapp.com",
  projectId: "health-app-ed269",
  storageBucket: "health-app-ed269.appspot.com",
  messagingSenderId: "957154504558",
  appId: "1:957154504558:web:7e6b13845731bd492c9b7f",
  measurementId: "G-JGBCQ960QG"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Test Firebase Authentication
const testFirebaseAuth = async () => {
  const testEmail = 'testuser3@example.com';
  const testPassword = 'Test@1234';

  try {
    // Test user signup
    const signupResult = await createUserWithEmailAndPassword(auth, testEmail, testPassword);
    console.log('Signup successful:', signupResult.user);

    // Test user login
    const loginResult = await signInWithEmailAndPassword(auth, testEmail, testPassword);
    console.log('Login successful:', loginResult.user);

    // Get ID token
    const idToken = await loginResult.user.getIdToken();
    console.log('ID Token:', idToken);
  } catch (error) {
    console.error('Error during Firebase Authentication test:', error);
  }
};

// Run the test
testFirebaseAuth();
