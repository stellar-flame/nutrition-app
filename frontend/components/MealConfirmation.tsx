import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { MealEntry } from '../types';

interface MealConfirmationProps {
  pendingMeal: MealEntry;
  saveMeal: (meal: MealEntry) => Promise<any>;
  setConversationHistory: React.Dispatch<React.SetStateAction<string[]>>;
  setPendingMeal: (meal: MealEntry | null) => void;
  setConversationId: (id: string | null) => void;
  setAwaitingConfirmation: (b: boolean) => void;
  setUserFeedback: (s: string) => void;
  cancelMeal: () => void;
}

const MealConfirmation: React.FC<MealConfirmationProps> = ({
  pendingMeal,
  saveMeal,
  setConversationHistory,
  setPendingMeal,
  setConversationId,
  setAwaitingConfirmation,
  setUserFeedback,
  cancelMeal,
}) => (
  <View style={styles.confirmationContainer}>
    <Text style={styles.confirmationText}>{pendingMeal.description}</Text>
    <Text style={styles.confirmationText}>{pendingMeal.assumptions}</Text>
    <Text style={styles.confirmationText}>
      Calories: {pendingMeal.calories.toFixed(0)}, Protein: {pendingMeal.protein?.toFixed(0)},
      Carbs: {pendingMeal.carbs?.toFixed(0)}, Fat: {pendingMeal.fat?.toFixed(0)},
      Sugar: {pendingMeal.sugar?.toFixed(0)}
    </Text>
    <View style={styles.confirmationButtons}>
      <TouchableOpacity
        style={[styles.iconButton, styles.confirmButton]}
        onPress={async () => {
          try {
            const savedMeal = await saveMeal(pendingMeal);
            setConversationHistory((prev) => [...prev, `Meal logged: ${savedMeal.description}`]);
            setPendingMeal(null);
            setConversationId(null);
            setAwaitingConfirmation(false);
            setUserFeedback('');
            setTimeout(() => setConversationHistory([]), 3000);
          } catch (error) {
            console.error('Error:', error);
            Alert.alert('Error', 'Failed to save meal');
          }
        }}
      >
        <Text style={styles.iconButtonText}>✓</Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.iconButton, styles.cancelButton]}
        onPress={cancelMeal}
      >
        <Text style={styles.iconButtonText}>✗</Text>
      </TouchableOpacity>
    </View>
  </View>
);

const styles = StyleSheet.create({
  confirmationContainer: {
    padding: 16,
    backgroundColor: '#e6f0ff',
    borderRadius: 8,
    marginBottom: 16,
  },
  confirmationText: {
    fontSize: 16,
    marginBottom: 8,
  },
  confirmationButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 10,
  },
  iconButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 10,
  },
  confirmButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#F44336',
  },
  iconButtonText: {
    fontSize: 24,
    color: 'white',
    fontWeight: 'bold',
  },
});

export default MealConfirmation;
