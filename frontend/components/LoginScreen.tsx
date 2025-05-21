import React, { useState } from 'react';
import { View, TextInput, Button, StyleSheet, Alert } from 'react-native';
import api from '../api/axios';
import { auth } from '../firebase/firebaseConfig'; // Corrected Firebase auth import
import { signInWithEmailAndPassword } from 'firebase/auth'; // Import signInWithEmailAndPassword from Firebase


const LoginScreen = ({ onLogin }: { onLogin: (idToken: string) => void }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSignUp, setIsSignUp] = useState(false);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [weight, setWeight] = useState('');
  const [height, setHeight] = useState('');


  
  const handleAuth = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please enter both email and password');
      return;
    }

    try {
      if (isSignUp) {
        if (!firstName || !lastName || !dateOfBirth || !weight || !height) {
          Alert.alert('Error', 'Please fill in all fields for signup');
          return;
        }
        await api.post('/auth/signup', {
          email,
          password,
          first_name: firstName,
          last_name: lastName,
          date_of_birth: dateOfBirth,
          weight: parseFloat(weight),
          height: parseFloat(height),
        });
        Alert.alert('Success', 'Account created. Please log in.');
        setIsSignUp(false);
      } else {
        // Log the email and password for debugging purposes (remove in production)
        console.log('Attempting login with:', { email, password });

        signInWithEmailAndPassword(auth, email, password)
            .then(async (userCredential) => {
                // Signed in 
                const idToken = await userCredential.user.getIdToken();
                console.log('User logged in:', userCredential.user);
                onLogin(idToken);   
            })
        .catch((error) => {
            const errorCode = error.code;
            const errorMessage = error.message;
            console.error('Authentication error:', error);
            console.error('Error code:', errorCode);
            console.error('Error message:', errorMessage);
        });
        // console.log('Logging in with:', { email, password });
        // const userCredential = await signInWithEmailAndPassword(auth, email, password);
        // console.log('User logged in:', userCredential);
        //  const idToken = await userCredential.user.getIdToken();
        // console.log('User logged in:', userCredential.user);
        // onLogin(idToken);
      }
    } catch (error) {
        console.error('Authentication error:', error);
      Alert.alert('Error', (error as any).response?.data?.detail || 'Something went wrong');
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      {isSignUp && (
        <>
          <TextInput
            style={styles.input}
            placeholder="First Name"
            value={firstName}
            onChangeText={setFirstName}
          />
          <TextInput
            style={styles.input}
            placeholder="Last Name"
            value={lastName}
            onChangeText={setLastName}
          />
          <TextInput
            style={styles.input}
            placeholder="Date of Birth (YYYY-MM-DD)"
            value={dateOfBirth}
            onChangeText={setDateOfBirth}
          />
          <TextInput
            style={styles.input}
            placeholder="Weight (kg)"
            value={weight}
            onChangeText={setWeight}
            keyboardType="numeric"
          />
          <TextInput
            style={styles.input}
            placeholder="Height (cm)"
            value={height}
            onChangeText={setHeight}
            keyboardType="numeric"
          />
        </>
      )}
      <Button title={isSignUp ? 'Sign Up' : 'Login'} onPress={handleAuth} />
      <Button
        title={isSignUp ? 'Switch to Login' : 'Switch to Sign Up'}
        onPress={() => setIsSignUp((prev) => !prev)}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 16 },
  input: { borderWidth: 1, borderColor: '#ccc', padding: 8, marginBottom: 16, borderRadius: 4 },
});

export default LoginScreen;
