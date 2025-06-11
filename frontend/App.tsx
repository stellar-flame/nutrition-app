import React, { useState, useEffect } from "react";
import {
  SafeAreaView,
  View,
  Text,
  Button,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Vibration,
} from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import api from "./api/axios";
import { auth } from "./firebase/firebaseConfig";
import { onAuthStateChanged, signOut, User } from "firebase/auth";

import HamburgerMenu from "./components/HamburgerMenu";
import MealList from "./components/MealList";
import NutritionSummary from "./components/NutritionSummary";
import LoginScreen from "./components/LoginScreen";
import ChatOverlay from "./components/ChatOverlay";
import { MealEntry, UserProfile, NutritionNeeds } from "./types";

export default function App() {
  useEffect(() => {
    fetch("https://identitytoolkit.googleapis.com")
      .then((res) => console.log("✅ Firebase reachable:", res.status))
      .catch((err) => console.error("❌ Firebase NOT reachable:", err));
  }, []);

  const [currentDate, setCurrentDate] = useState(new Date());
  const [inputText, setInputText] = useState("");
  const [meals, setMeals] = useState<MealEntry[]>([]);
  const [loading, setLoading] = useState(false);

  // State for conversational logging
  const [pendingMeal, setPendingMeal] = useState<MealEntry | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [userFeedback, setUserFeedback] = useState("");
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);

  // Add state for user authentication
  const [user, setUser] = useState<User | null>(null);
  const [isAppInitializing, setIsAppInitializing] = useState(true);

  const isToday = (date: Date): boolean => {
    const today = new Date();
    return (
      date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear()
    );
  };

  const [userProfile, setUserProfile] = useState<UserProfile>({
    firstName: "",
    lastName: "",
    dateOfBirth: "",
    weight: "",
    height: "",
  });

  const [nutritionNeeds, setNutritionNeeds] = useState<NutritionNeeds>({
    calories: 0,
    protein: 0,
    fiber: 0,
    fat: 0,
    carbs: 0,
    sugar: 0,
  });

  // Add state for chat overlay visibility
  const [isChatVisible, setIsChatVisible] = useState(false);

  // Show chat overlay when meal confirmation is needed
  useEffect(() => {
    if (awaitingConfirmation && pendingMeal) {
      setIsChatVisible(true);
    }
  }, [awaitingConfirmation, pendingMeal]);

  const toggleChat = () => {
    setIsChatVisible(!isChatVisible);
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setIsAppInitializing(false);
    });
    return () => unsubscribe();
  }, []);
  useEffect(() => {
    fetchMealsFromBackend();
    fetchUserProfile();
    fetchNutritionNeeds();
  }, [currentDate, user]);

  const handleLogin = async (idToken: string) => {
    try {
      // Send the ID token to the backend for verification
      const { data } = await api.get("/auth/verify", {
        headers: { Authorization: `Bearer ${idToken}` },
      });
      console.log("User verified:", data);
      setUser({ uid: data.uid } as User);
    } catch (error) {
      console.error("Token verification failed:", error);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
      console.log("User logged out");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  const fetchUserProfile = async () => {
    if (!user?.uid) return;
    try {
      const { data } = await api.get(`/users/${user.uid}`);
      setUserProfile({
        firstName: data.first_name,
        lastName: data.last_name,
        dateOfBirth: data.date_of_birth,
        weight: data.weight.toString(),
        height: data.height.toString(),
      });
    } catch (error) {
      console.error("Error fetching user profile:", error);
    }
  };

  const updateUserProfile = async (updatedProfile: UserProfile) => {
    if (!user?.uid) return;
    try {
      // Convert front-end model to back-end model
      const backendProfile = {
        first_name: updatedProfile.firstName,
        last_name: updatedProfile.lastName,
        date_of_birth: updatedProfile.dateOfBirth, // Keeping as string, backend will parse
        weight: parseFloat(updatedProfile.weight),
        height: parseFloat(updatedProfile.height),
      };

      // Send updated profile to backend
      await api.put(`/users/${user.uid}`, backendProfile);

      // Update local state
      setUserProfile(updatedProfile);
      console.log("Profile updated successfully");
    } catch (error) {
      console.error("Error updating profile:", error);
      // Fetch current profile to reset state if update failed
      fetchUserProfile();
    }
  };

  const fetchNutritionNeeds = async () => {
    if (!user?.uid) return;
    try {
      const { data } = await api.get(`/users/${user.uid}/nutrition-needs`);
      setNutritionNeeds({
        calories: data.calories,
        protein: data.protein,
        fiber: data.fiber,
        fat: data.fat,
        carbs: data.carbs,
        sugar: data.sugar,
      });
    } catch (error) {
      console.error("Error fetching nutrition needs:", error);
    }
  };

  const fetchMealsFromBackend = async () => {
    if (!user?.uid) return;
    try {
      // Keep using just the date part for searching meals by day
      const dateStr = currentDate.toISOString().split("T")[0];
      const { data } = await api.get(`/meals/${user.uid}`, {
        params: { search_date: dateStr },
      });
      if (data.meals) {
        const cleanedMeals = data.meals.map((meal: any) => ({
          ...meal,
          calories: Number(meal.calories),
          protein: Number(meal.protein),
          fiber: Number(meal.fiber),
          carbs: Number(meal.carbs),
          fat: Number(meal.fat),
          sugar: Number(meal.sugar),
        }));
        setMeals(cleanedMeals);
      }
    } catch (error) {
      console.error("Error fetching meals from backend:", error);
      setMeals([]);
    }
  };

  // For handling food input and conversation
  const handleFoodInput = async (input: string) => {
    setLoading(true);

    try {
      const { data: result } = await api.post("/openai/chat", {
        user_id: user?.uid, // Dynamic user ID
        description: input,
        conversation_id: conversationId,
        user_feedback: userFeedback || undefined,
        model: "gpt-4",
        temperature: 0,
        max_tokens: 150,
      });

      // Always use the conversation ID from the response
      setConversationId(result.conversation_id);

      if (result.message) {
        // Add AI's message to conversation history
        console.log("Message: " + result.message);
        setConversationHistory((prev) => [...prev, `App: ${result.message}`]);
        // Add slight vibration feedback when receiving message
        Vibration.vibrate(30);
      } else if (result.meal) {
        console.log("Meal: " + result.message);
        setPendingMeal(result.meal);
        setAwaitingConfirmation(true);

        const mealInfo = `App: Found "${result.meal.description}" (${result.meal.calories} cal)`;

        setConversationHistory((prev) => [...prev, mealInfo]);
        // Add slightly stronger vibration for meal confirmation
        Vibration.vibrate(50);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  // For saving confirmed meals
  const saveMeal = async (meal: MealEntry) => {
    try {
      // Format timestamp as ISO string with time (YYYY-MM-DDTHH:MM:SS)
      const timestamp = new Date(currentDate).toISOString();
      const { data: savedMeal } = await api.post("/meals/", {
        user_id: user?.uid, // Dynamic user ID
        description: meal.description,
        calories: meal.calories,
        protein: meal.protein,
        fiber: meal.fiber,
        carbs: meal.carbs,
        fat: meal.fat,
        sugar: meal.sugar,
        timestamp: timestamp, // Full ISO datetime format
      });
      setMeals((prev) => [savedMeal, ...prev]);

      // If we have a conversation ID, delete the thread
      if (conversationId) {
        try {
          await api.delete(`/openai/thread/${conversationId}`);
          console.log("Thread deleted successfully");
        } catch (threadError) {
          console.error("Failed to delete thread:", threadError);
          // Non-blocking error - we still want to continue even if thread deletion fails
        }
      }
      setPendingMeal(null);
      setConversationId(null);
      setAwaitingConfirmation(false);
      setUserFeedback("");
      setConversationHistory([]); // Always clear conversation history after saving a meal

      return savedMeal;
    } catch (error) {
      throw new Error("Failed to save meal");
    }
  };

  // Handle user input
  const addMeal = async () => {
    if (!inputText.trim()) return;

    const input = inputText.trim();
    setInputText(""); // Clear input immediately

    // Add to conversation history
    if (awaitingConfirmation) {
      // If we're awaiting confirmation, append to history
      setConversationHistory((prev) => [...prev, `You: ${input}`]);
      setUserFeedback(input);
    } else if (conversationId && conversationHistory.length > 0) {
      // If we have an existing conversation, append to history
      setConversationHistory((prev) => [...prev, `You: ${input}`]);
      setUserFeedback("");
    } else {
      // Start a new conversation
      setConversationHistory([`You: ${input}`]);
      setUserFeedback("");
    }

    // Add slight vibration feedback when sending message
    Vibration.vibrate(20);

    await handleFoodInput(input);
  };

  const cancelMeal = (keepHistory: boolean = false) => {
    setPendingMeal(null);
    setConversationId(null); // Always clear conversation ID
    setAwaitingConfirmation(false);
    setUserFeedback("");

    // Only clear conversation history when:
    // 1. keepHistory is false AND
    // 2. We're not in the middle of adding more information to a pending meal
    if (!keepHistory) {
      setConversationHistory([]);
    }

    setInputText("");
  };

  const handleDeleteMeal = async (id: string) => {
    try {
      await api.delete(`/meals/${id}`);
      setMeals((prev) => prev.filter((meal) => meal.id !== id));
    } catch (error) {
      console.error("Failed to delete meal");
    }
  };

  // Define direct functions for changing dates
  function changeDateByOffset(offset: number) {
    const newDate = new Date(currentDate);
    newDate.setDate(newDate.getDate() + offset);
    setCurrentDate(newDate);
  }

  // Calculate totals
  const totals = meals.reduce(
    (acc, meal) => {
      acc.calories = (acc.calories ?? 0) + (meal.calories ?? 0);
      acc.protein = (acc.protein ?? 0) + (meal.protein ?? 0);
      acc.fiber = (acc.fiber ?? 0) + (meal.fiber ?? 0);
      acc.carbs = (acc.carbs ?? 0) + (meal.carbs ?? 0);
      acc.fat = (acc.fat ?? 0) + (meal.fat ?? 0);
      acc.sugar = (acc.sugar ?? 0) + (meal.sugar ?? 0);
      return acc;
    },
    { calories: 0, protein: 0, fiber: 0, carbs: 0, fat: 0, sugar: 0 }
  );
  // Conditionally render LoginScreen or Main App
  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  if (isAppInitializing) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaView style={styles.container}>
        <HamburgerMenu userProfile={userProfile} onSave={updateUserProfile} />
        <View style={styles.dateNavigationContainer}>
          <Button title="←" onPress={() => changeDateByOffset(-1)} />
          <Text
            style={
              isToday(currentDate)
                ? styles.currentDateHighlight
                : styles.currentDate
            }
          >
            {currentDate.toDateString()}
          </Text>
          <Button title="→" onPress={() => changeDateByOffset(1)} />
        </View>
        <Text style={styles.title}>Nutrition App - Calorie Tracker</Text>

        <NutritionSummary totals={totals} nutritionNeeds={nutritionNeeds} />

        <MealList meals={meals} onDeleteMeal={handleDeleteMeal} />

        {/* Floating action button to toggle chat - hide when chat is visible */}
        {!isChatVisible && (
          <TouchableOpacity style={styles.chatButton} onPress={toggleChat}>
            <Text style={styles.chatButtonText}>💬</Text>
          </TouchableOpacity>
        )}

        {/* Chat overlay */}
        <ChatOverlay
          isVisible={isChatVisible}
          onClose={() => setIsChatVisible(false)}
          conversationHistory={conversationHistory}
          inputText={inputText}
          setInputText={setInputText}
          addMeal={addMeal}
          loading={loading}
          pendingMeal={pendingMeal}
          saveMeal={saveMeal}
          setConversationHistory={setConversationHistory}
          cancelMeal={cancelMeal}
          awaitingConfirmation={awaitingConfirmation}
        />
      </SafeAreaView>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: "#fff" },
  dateNavigationContainer: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 8,
  },
  currentDate: {
    fontSize: 18,
    fontWeight: "600",
    textAlign: "center",
    marginHorizontal: 12,
  },
  currentDateHighlight: {
    fontSize: 20,
    fontWeight: "bold",
    textAlign: "center",
    marginHorizontal: 12,
    color: "#007AFF",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 16,
    textAlign: "center",
  },
  chatButton: {
    position: "absolute",
    bottom: 20,
    right: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#007AFF",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 5,
    zIndex: 999,
  },
  chatButtonText: {
    fontSize: 30,
    color: "white",
  },
});
