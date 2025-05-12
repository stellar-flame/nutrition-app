import React, { useState, useEffect } from 'react';
import { SafeAreaView, View, Text, TextInput, Button, FlatList, StyleSheet, Alert } from 'react-native';
import HamburgerMenu from './components/HamburgerMenu';

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

  const [userProfile, setUserProfile] = useState({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    weight: '',
    height: '',
  });

  const [nutritionNeeds, setNutritionNeeds] = useState({
    calories: 0,
    protein: 0,
    fat: 0,
    carbs: 0,
  });

  useEffect(() => {
    fetchMealsFromBackend();
    fetchUserProfile();
    fetchNutritionNeeds();
  }, []);

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`http://localhost:8000/users/1`); // Using user ID 1 for demo
      if (!response.ok) {
        throw new Error('Failed to fetch user profile');
      }
      const data = await response.json();
      setUserProfile({
        firstName: data.first_name,
        lastName: data.last_name,
        dateOfBirth: data.date_of_birth,
        weight: data.weight.toString(),
        height: data.height.toString(),
      });
    } catch (error) {
      console.error('Error fetching user profile:', error);
    }
  };

  const fetchNutritionNeeds = async () => {
    try {
      const response = await fetch(`http://localhost:8000/users/1/nutrition-needs`);
      if (!response.ok) {
        throw new Error('Failed to fetch nutrition needs');
      }
      const data = await response.json();
      setNutritionNeeds({
        calories: data.calories,
        protein: data.protein,
        fat: data.fat,
        carbs: data.carbs,
      });
    } catch (error) {
      console.error('Error fetching nutrition needs:', error);
    }
  };

  const saveUserProfile = async (profile: any) => {
    try {
      const response = await fetch('http://localhost:8000/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: profile.firstName,
          last_name: profile.lastName,
          date_of_birth: profile.dateOfBirth,
          weight: parseFloat(profile.weight),
          height: parseFloat(profile.height),
        }),
      });
      if (!response.ok) {
        throw new Error('Failed to save user profile');
      }
      const data = await response.json();
      setUserProfile({
        firstName: data.first_name,
        lastName: data.last_name,
        dateOfBirth: data.date_of_birth,
        weight: data.weight.toString(),
        height: data.height.toString(),
      });
      Alert.alert('Success', 'Profile saved successfully');
      fetchNutritionNeeds(); // Refresh nutrition needs after profile update
    } catch (error) {
      console.error('Error saving user profile:', error);
      Alert.alert('Error', 'Failed to save profile');
    }
  };

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
      <HamburgerMenu userProfile={userProfile} onSave={saveUserProfile} />
      <Text style={styles.title}>Health App - Calorie Tracker</Text>

      <View style={styles.nutritionTable}>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>
            Calories {totals.calories.toFixed(0)}/{nutritionNeeds.calories}
          </Text>
          <Text style={[styles.nutritionValue, styles.remaining]}>
            {Math.max(nutritionNeeds.calories - totals.calories, 0)}
          </Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>
            Protein (g) {totals.protein.toFixed(0)}/{nutritionNeeds.protein}
          </Text>
          <Text style={[styles.nutritionValue, styles.remaining]}>
            {Math.max(nutritionNeeds.protein - totals.protein, 0)}
          </Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>
            Carbs (g) {totals.carbs.toFixed(0)}/{nutritionNeeds.carbs}
          </Text>
          <Text style={[styles.nutritionValue, styles.remaining]}>
            {Math.max(nutritionNeeds.carbs - totals.carbs, 0)}
          </Text>
        </View>
        <View style={styles.nutritionRow}>
          <Text style={styles.nutritionLabel}>
            Fat (g) {totals.fat.toFixed(0)}/{nutritionNeeds.fat}
          </Text>
          <Text style={[styles.nutritionValue, styles.remaining]}>
            {Math.max(nutritionNeeds.fat - totals.fat, 0)}
          </Text>
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
  remaining: { fontSize: 16, color: 'red' },
  inputContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  input: { flex: 1, borderColor: '#ccc', borderWidth: 1, borderRadius: 4, padding: 8, marginRight: 8 },
  mealItem: { padding: 12, borderBottomColor: '#eee', borderBottomWidth: 1 },
  mealDescription: { fontSize: 16, fontWeight: '500' },
  mealNutrition: { fontSize: 14, color: '#555' },
  emptyText: { textAlign: 'center', color: '#999', marginTop: 20 },
  clarificationContainer: { padding: 10, backgroundColor: '#fff3cd', borderColor: '#ffeeba', borderWidth: 1, borderRadius: 4, marginBottom: 16 },
  clarificationText: { color: '#856404', fontSize: 14 },
});
