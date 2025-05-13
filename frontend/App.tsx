import React, { useState, useEffect } from 'react';
import { SafeAreaView, View, Text, TextInput, Button, FlatList, StyleSheet, Alert } from 'react-native';
import { GestureHandlerRootView, GestureDetector, Gesture } from 'react-native-gesture-handler';
import HamburgerMenu from './components/HamburgerMenu';

// const mockUser = {
//   id: 'user123',
//   email: 'user@example.com',
// };

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

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

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
    sugar: 0,
  });

  const [currentDate, setCurrentDate] = useState(new Date());

  useEffect(() => {
    fetchMealsFromBackend();
    fetchUserProfile();
    fetchNutritionNeeds();
  }, [currentDate]);

  // Refetch functions
  // Line 75: fetchMealsFromBackend
  // Line 79: fetchUserProfile
  // Line 80: fetchNutritionNeeds

  const fetchUserProfile = async () => {
    try {
      const response = await fetch(`http://192.168.0.9:8000/users/1`);
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
      const response = await fetch(`http://192.168.0.9:8000/users/1/nutrition-needs`);
      if (!response.ok) {
        throw new Error('Failed to fetch nutrition needs');
      }
      const data = await response.json();
      setNutritionNeeds({
        calories: data.calories,
        protein: data.protein,
        fat: data.fat,
        carbs: data.carbs,
        sugar: data.sugar,
      });
    } catch (error) {
      console.error('Error fetching nutrition needs:', error);
    }
  };

  const fetchMealsFromBackend = async () => {
    try {
      const dateStr = currentDate.toISOString().split('T')[0];
      console.log(dateStr)
      const response = await fetch(`http://192.168.0.9:8000/meals/1?search_date=${dateStr}`);
      if (!response.ok) {
        throw new Error('Failed to fetch meals from backend');
      }
      const data = await response.json();
      if (data.meals) {
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

  const fetchNutrition = async (description: string): Promise<any> => {
    setLoading(true);
    try {
      const response = await fetch('http://192.168.0.9:8000/openai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: "1",
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

  const panGesture = Gesture.Pan()
    .onEnd((event) => {
      const { translationX } = event;
      if (translationX > 50) {
        // Swipe right: previous day
        setCurrentDate(prev => {
          const newDate = new Date(prev);
          newDate.setDate(newDate.getDate() - 1);
          return newDate;
        });
      } else if (translationX < -50) {
        // Swipe left: next day
        setCurrentDate(prev => {
          const newDate = new Date(prev);
          newDate.setDate(newDate.getDate() + 1);
          return newDate;
        });
      }
    });

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
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector gesture={panGesture}>
        <SafeAreaView style={styles.container}>
          <HamburgerMenu userProfile={userProfile} onSave={setUserProfile} />
          <View style={styles.dateNavigationContainer}>
            <Button title="←" onPress={() => {
              setCurrentDate(prev => {
                const newDate = new Date(prev);
                newDate.setDate(newDate.getDate() - 1);
                return newDate;
              });
            }} />
            <Text style={isToday(currentDate) ? styles.currentDateHighlight : styles.currentDate}>{currentDate.toDateString()}</Text>
            <Button title="→" onPress={() => {
              setCurrentDate(prev => {
                const newDate = new Date(prev);
                newDate.setDate(newDate.getDate() + 1);
                return newDate;
              });
            }} />
          </View>
          <Text style={styles.title}>Health App - Calorie Tracker</Text>

          <View style={styles.nutritionTable}>
            <View style={styles.nutritionRow}>
              <Text style={styles.nutritionLabel}>Calories</Text>
              <View style={styles.nutritionValuesContainer}>
                <Text style={[styles.nutritionValue, styles.nutritionValueColumn]}>
                  {totals.calories.toFixed(0)}/{nutritionNeeds.calories}
                </Text>
                <Text style={[totals.calories < nutritionNeeds.calories ? styles.pos_remaining : styles.neg_remaining, styles.nutritionValueColumn]}>
                  {Math.round(nutritionNeeds.calories - totals.calories)}
                </Text>
              </View>
            </View>
            <View style={styles.nutritionRow}>
              <Text style={styles.nutritionLabel}>Protein (g)</Text>
              <View style={styles.nutritionValuesContainer}>
                <Text style={[styles.nutritionValue, styles.nutritionValueColumn]}>
                  {totals.protein.toFixed(0)}/{nutritionNeeds.protein}
                </Text>
                <Text style={[totals.protein < nutritionNeeds.protein ? styles.pos_remaining : styles.neg_remaining, styles.nutritionValueColumn]}>
                  {Math.round(nutritionNeeds.protein - totals.protein)}
                </Text>
              </View>
            </View>
            <View style={styles.nutritionRow}>
              <Text style={styles.nutritionLabel}>Carbs (g)</Text>
              <View style={styles.nutritionValuesContainer}>
                <Text style={[styles.nutritionValue, styles.nutritionValueColumn]}>
                  {totals.carbs.toFixed(0)}/{nutritionNeeds.carbs}
                </Text>
                <Text style={[totals.carbs < nutritionNeeds.carbs ? styles.pos_remaining : styles.neg_remaining, styles.nutritionValueColumn]}>
                  {Math.round(nutritionNeeds.carbs - totals.carbs)}
                </Text>
              </View>
            </View>
            <View style={styles.nutritionRow}>
              <Text style={styles.nutritionLabel}>Fat (g)</Text>
              <View style={styles.nutritionValuesContainer}>
                <Text style={[styles.nutritionValue, styles.nutritionValueColumn]}>
                  {totals.fat.toFixed(0)}/{nutritionNeeds.fat}
                </Text>
                <Text style={[totals.fat < nutritionNeeds.fat ? styles.pos_remaining : styles.neg_remaining, styles.nutritionValueColumn]}>
                  {Math.round(nutritionNeeds.fat - totals.fat)}
                </Text>
              </View>
            </View>
            <View style={styles.nutritionRow}>
              <Text style={styles.nutritionLabel}>Sugar (g)</Text>
              <View style={styles.nutritionValuesContainer}>
                <Text style={[styles.nutritionValue, styles.nutritionValueColumn]}>{totals.sugar.toFixed(0)}</Text>
                <Text style={[totals.sugar < nutritionNeeds.sugar ? styles.pos_remaining : styles.neg_remaining, styles.nutritionValueColumn]}>
                  {Math.round(nutritionNeeds.sugar - totals.sugar)}
                </Text>
              </View>
            </View>
          </View>

          <FlatList
            data={meals}
            keyExtractor={(item) => item.id.toString()}
            renderItem={({ item }) => (
              <View style={styles.mealItem}>
                <Text style={styles.mealDescription}>{item.description}</Text>
                <Text style={styles.mealNutrition}>
                  Calories: {item.calories.toFixed(0)}, Protein: {item.protein?.toFixed(0)}, Carbs: {item.carbs?.toFixed(0)}, Fat: {item.fat?.toFixed(0)}, Sugar: {item.sugar?.toFixed(0)}
                </Text>
              </View>
            )}
            ListEmptyComponent={<Text style={styles.emptyText}>No meals logged for this date.</Text>}
          />

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
        </SafeAreaView>
      </GestureDetector>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  dateNavigationContainer: { flexDirection: 'row', justifyContent: 'center', alignItems: 'center', marginBottom: 8 },
  currentDate: { fontSize: 18, fontWeight: '600', textAlign: 'center', marginHorizontal: 12 },
  currentDateHighlight: { fontSize: 20, fontWeight: 'bold', textAlign: 'center', marginHorizontal: 12, color: '#007AFF' },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 16, textAlign: 'center' },
  nutritionTable: { marginBottom: 16, borderWidth: 1, borderColor: '#ccc', borderRadius: 4, padding: 8 },
  nutritionRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  nutritionLabel: { fontSize: 16, fontWeight: '600' },
  nutritionValue: { fontSize: 16 },
  nutritionValuesContainer: { flexDirection: 'row', justifyContent: 'flex-end', width: 160 },
  nutritionValueColumn: { flex: 1, textAlign: 'right' },
  neg_remaining: { fontSize: 16, color: 'red' },
  pos_remaining: { fontSize: 16, color: 'green' },
  inputContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  input: { flex: 1, borderColor: '#ccc', borderWidth: 1, borderRadius: 4, padding: 8, paddingLeft: 12, marginRight: 8 },
  mealItem: { padding: 12, borderBottomColor: '#eee', borderBottomWidth: 1 },
  mealDescription: { fontSize: 16, fontWeight: '500' },
  mealNutrition: { fontSize: 14, color: '#555' },
  emptyText: { textAlign: 'center', color: '#999', marginTop: 20 },
  clarificationContainer: { padding: 10, backgroundColor: '#fff3cd', borderColor: '#ffeeba', borderWidth: 1, borderRadius: 4, marginBottom: 16 },
  clarificationText: { color: '#856404', fontSize: 14 },
});
