import React from 'react';
import { View, TextInput, TouchableOpacity, Text, StyleSheet } from 'react-native';

interface MealInputProps {
  inputText: string;
  setInputText: (text: string) => void;
  addMeal: () => void;
  loading: boolean;
}

const MealInput: React.FC<MealInputProps> = ({ inputText, setInputText, addMeal, loading }) => (
  <View style={styles.inputContainer}>
    <TextInput
      style={styles.input}
      placeholder="What did you eat?"
      value={inputText}
      onChangeText={setInputText}
      editable={!loading}
    />
    <TouchableOpacity
      style={[styles.sendButton, loading && styles.sendButtonDisabled]}
      onPress={addMeal}
      disabled={loading}
    >
      <Text style={styles.sendButtonText}>{loading ? '...' : '➤'}</Text>
    </TouchableOpacity>
  </View>
);

const styles = StyleSheet.create({
  inputContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  input: { flex: 1, borderColor: '#ccc', borderWidth: 1, borderRadius: 4, padding: 8, paddingLeft: 12, marginRight: 8 },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
  sendButtonText: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
});

export default MealInput;
