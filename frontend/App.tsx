import React, { useState, useEffect } from 'react';
import { SafeAreaView, View, Text, TextInput, Button, FlatList, StyleSheet, Alert } from 'react-native';

// Placeholder for user authentication state
const mockUser = {
  id: 'user123',
  email: 'user@example.com',
};

interface MealEntry {
  id: string;
  description: string;
  calories: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  sugar?: number;
}

export default function App() {
  const [inputText, setInputText] = useState('');
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [clarification, setClarification] = useState('');

  useEffect(() => {
    fetchMealsFromBackend();
  }, []);

  // Fetch meals from backend server
  const fetchMealsFromBackend = async () => {
    try {
      const response = await fetch(`http://localhost:8000/meals/${mockUser.id}`);
      if (!response.ok) {
        throw new Error('Failed to fetch meals from backend');
      }
      const data = await response.json();
      if (data.meals) {
        // Convert numeric fields to numbers if needed
        const cleanedMeals = data.meals.map((meal: any) => ({
          ...meal,
          calories: Number(meal.calories),
          protein: Number(meal.protein),
          carbs: Number(meal.carbs),
          fat: Number(meal.fat),
          sugar: Number(meal.sugar),
        }));
        setMeals(cleanedMeals);
      }
    } catch (error) {
      console.error('Error fetching meals from backend:', error);
      setMeals([]);
    }
  };

  // Call backend server to get nutritional info and save meal
  const fetchNutrition = async (description: string): Promise<any> => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/openai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: mockUser.id,
          description,
          model: 'gpt-4',
          temperature: 0,
          max_tokens: 150,
        }),
      });

      if (!response.ok) {
        console.error("Backend API error:", await response.text());
        throw new Error("API call failed");
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error("Error fetching nutritional information:", error);
      Alert.alert('Error', 'Failed to fetch nutritional information.');
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Add meal entry or handle clarification
  const addMeal = async () => {
    if (!inputText.trim()) return;
    const result = await fetchNutrition(inputText.trim());
    if (result) {
      if (result.meal) {
        const newMeal = {
          ...result.meal,
          calories: Number(result.meal.calories),
          protein: Number(result.meal.protein),
          carbs: Number(result.meal.carbs),
          fat: Number(result.meal.fat),
          sugar: Number(result.meal.sugar),
        };
        const newMeals = [newMeal, ...meals];
        setMeals(newMeals);
        setInputText('');
        setClarification('');
      } else if (result.clarification) {
        setClarification(result.clarification);
      }
    }
  };

  // Calculate totals
  const totals = meals.reduce(
    (acc, meal) => {
      acc.calories = (acc.calories ?? 0) + (meal.calories ?? 0);
      acc.protein = (acc.protein ?? 0) + (meal.protein ?? 0);
      acc.carbs = (acc.carbs ?? 0) + (meal.carbs ?? 0);
      acc.fat = (acc.fat ?? 0) + (meal.fat ?? 0);
      acc.sugar = (acc.sugar ?? 0) + (meal.sugar ?? 0);
      return acc;
    },
    { calories: 0, protein: 0, carbs: 0, fat: 0, sugar: 0 }
  );

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Health App - Calorie Tracker</Text>

      <View style={styles.nutritionTable}>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>Calories</Text>
          <Text style={styles.nutritionValue}>{totals.calories.toFixed(0)}</Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>Protein (g)</Text>
          <Text style={styles.nutritionValue}>{totals.protein.toFixed(0)}</Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>Carbs (g)</Text>
          <Text style={styles.nutritionValue}>{totals.carbs.toFixed(0)}</Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>Fat (g)</Text>
          <Text style={styles.nutritionValue}>{totals.fat.toFixed(0)}</Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>Sugar (g)</Text>
          <Text style={styles.nutritionValue}>{totals.sugar.toFixed(0)}</Text>
        </View>
      </View>

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          placeholder="What did you eat?"
          value={inputText}
          onChangeText={setInputText}
          editable={!loading}
        />
        <Button title={loading ? 'Loading...' : 'Add'} onPress={addMeal} disabled={loading} />
      </View>
      {clarification ? (
        <View style={styles.clarificationContainer}>
          <Text style={styles.clarificationText}>{clarification}</Text>
        </View>
      ) : null}

      <FlatList
        data={meals}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.mealItem}>
            <Text style={styles.mealDescription}>{item.description}</Text>
            <Text style={styles.mealNutrition}>
              {item.calories} cal | {item.protein}g P | {item.carbs}g C | {item.fat}g F | {item.sugar}g S
            </Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.emptyText}>No meals added yet.</Text>}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 16, textAlign: 'center' },
  nutritionTable: { marginBottom: 16, borderWidth: 1, borderColor: '#ccc', borderRadius: 4, padding: 8 },
  nutritionRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  nutritionLabel: { fontSize: 16, fontWeight: '600' },
  nutritionValue: { fontSize: 16 },
  inputContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  input: { flex: 1, borderColor: '#ccc', borderWidth: 1, borderRadius: 4, padding: 8, marginRight: 8 },
  mealItem: { padding: 12, borderBottomColor: '#eee', borderBottomWidth: 1 },
  mealDescription: { fontSize: 16, fontWeight: '500' },
  mealNutrition: { fontSize: 14, color: '#555' },
  emptyText: { textAlign: 'center', color: '#999', marginTop: 20 },
  clarificationContainer: { padding: 10, backgroundColor: '#fff3cd', borderColor: '#ffeeba', borderWidth: 1, borderRadius: 4, marginBottom: 16 },
  clarificationText: { color: '#856404', fontSize: 14 },
});
