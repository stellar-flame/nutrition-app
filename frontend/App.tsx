import React, { useState, useEffect } from 'react';
import { SafeAreaView, View, Text, Button, StyleSheet, Alert } from 'react-native';
import { GestureHandlerRootView, GestureDetector, Gesture } from 'react-native-gesture-handler';
import api from './api/axios';
import HamburgerMenu from './components/HamburgerMenu';
import MealList from './components/MealList';
import MealInput from './components/MealInput';
import NutritionSummary from './components/NutritionSummary';
import ConversationHistory from './components/ConversationHistory';
import MealConfirmation from './components/MealConfirmation';
import { MealEntry, UserProfile, NutritionNeeds } from './types';

export default function App() {
  const [inputText, setInputText] = useState('');
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [loading, setLoading] = useState(false);

  // State for conversational logging
  const [pendingMeal, setPendingMeal] = useState<MealEntry | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [userFeedback, setUserFeedback] = useState('');
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const [userProfile, setUserProfile] = useState<UserProfile>({
    firstName: '',
    lastName: '',
    dateOfBirth: '',
    weight: '',
    height: '',
  });

  const [nutritionNeeds, setNutritionNeeds] = useState<NutritionNeeds>({
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

  const fetchUserProfile = async () => {
    try {
      const { data } = await api.get('/users/1');
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
      const { data } = await api.get('/users/1/nutrition-needs');
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
      const { data } = await api.get(`/meals/1`, {
        params: { search_date: dateStr }
      });
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

  // For handling food input and conversation
  const handleFoodInput = async (input: string) => {
    setLoading(true);
    
    try {
      const { data: result } = await api.post('/openai/chat', {
        user_id: "1",
        description: input,
        conversation_id: conversationId,
        user_feedback: userFeedback || undefined,
        model: 'gpt-4',
        temperature: 0,
        max_tokens: 150,
      });
      
      // Always use the conversation ID from the response
      setConversationId(result.conversation_id);
      
      if (result.message) {
        // Add AI's message to conversation history
        console.log("Message: " + result.message)
        setConversationHistory(prev => [...prev, `App: ${result.message}`]);
      } else if (result.meal) {
        console.log("Meal: " + result.message)
        setPendingMeal(result.meal);
        setAwaitingConfirmation(true);
        
        const mealInfo = `App: Found "${result.meal.description}" (${result.meal.calories} cal)`;

        setConversationHistory(prev => [...prev, mealInfo]);
      }
    } catch (error) {
      console.error('Error:', error);
      Alert.alert('Error', 'Failed to process food input');
    } finally {
      setLoading(false);
    }
  };

  // For saving confirmed meals
  const saveMeal = async (meal: MealEntry) => {
    try {
      const { data: savedMeal } = await api.post('/meals/', {
        user_id: "1",
        description: meal.description,
        calories: meal.calories,
        protein: meal.protein,
        carbs: meal.carbs,
        fat: meal.fat,
        sugar: meal.sugar,
      });
      setMeals(prev => [savedMeal, ...prev]);
      return savedMeal;
    } catch (error) {
      throw new Error('Failed to save meal');
    }
  };

  // Handle user input
  const addMeal = async () => {
    if (!inputText.trim()) return;
    
    const input = inputText.trim();
    setInputText(''); // Clear input immediately
    
    // Add to conversation history
    if (awaitingConfirmation) {
      setConversationHistory(prev => [...prev, `You: ${input}`]);
      setUserFeedback(input);
    } else {
      // Start a new conversation
      setConversationHistory([`You: ${input}`]);
      setUserFeedback('');
    }
    
    await handleFoodInput(input);
  };

  const cancelMeal = () => {
    setPendingMeal(null);
    setConversationId(null);
    setAwaitingConfirmation(false);
    setUserFeedback('');
    setConversationHistory([]);
    setInputText('');
  };

  const handleDeleteMeal = async (id: string) => {
    try {
      await api.delete(`/meals/${id}`);
      setMeals((prev) => prev.filter((meal) => meal.id !== id));
    } catch (error) {
      Alert.alert('Error', 'Failed to delete meal');
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

          <NutritionSummary totals={totals} nutritionNeeds={nutritionNeeds} />
          <MealInput inputText={inputText} setInputText={setInputText} addMeal={addMeal} loading={loading} />
          <ConversationHistory conversationHistory={conversationHistory} />
          {awaitingConfirmation && pendingMeal ? (
            <MealConfirmation
              pendingMeal={pendingMeal}
              saveMeal={saveMeal}
              setConversationHistory={setConversationHistory}
              setPendingMeal={setPendingMeal}
              setConversationId={setConversationId}
              setAwaitingConfirmation={setAwaitingConfirmation}
              setUserFeedback={setUserFeedback}
              cancelMeal={cancelMeal}
            />
          ) : (
            <MealList meals={meals} onDeleteMeal={handleDeleteMeal} />
          )}
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
});
