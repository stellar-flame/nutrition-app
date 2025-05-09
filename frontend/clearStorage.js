import AsyncStorage from '@react-native-async-storage/async-storage';

async function clearStorage() {
  try {
    await AsyncStorage.removeItem("meals-user123");
    console.log('AsyncStorage key "meals-user123" cleared successfully.');
  } catch (error) {
    console.error('Failed to clear AsyncStorage key:', error);
  }
}

clearStorage();
