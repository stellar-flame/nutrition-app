import React, { useState, useEffect } from "react";
import {
  SafeAreaView,
  View,
  Text,
  Button,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import api from "./api/axios";
import { useAuth } from "./hooks/useAuth"; // Import our new custom hook
import { useMeals } from './hooks/useMeals';
import HamburgerMenu from "./components/HamburgerMenu";
import MealList from "./components/MealList";
import NutritionSummary from "./components/NutritionSummary";
import LoginScreen from "./components/LoginScreen";
import ChatOverlay from "./components/ChatOverlay";
import { UserProfile, NutritionNeeds } from "./types";
import { User } from 'firebase/auth';

export default function App() {
  // ✨ NEW: Use our custom hook instead of individual useState calls
  const { user, isLoading: isAuthLoading, login, logout, error: authError } = useAuth();

  useEffect(() => {
    fetch("https://identitytoolkit.googleapis.com")
      .then((res) => console.log("✅ Firebase reachable:", res.status))
      .catch((err) => console.error("❌ Firebase NOT reachable:", err));
  }, []);

  const [currentDate, setCurrentDate] = useState(new Date());
  
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


  const toggleChat = () => {
    setIsChatVisible(!isChatVisible);
  };


 
  // ✨ NEW: Use the login function from our custom hook
  const handleLogin = async (idToken: string) => {
    try {
      await login(idToken); // Much cleaner!
    } catch (error) {
      console.error("Login failed:", error);
      // The error is already handled in the useAuth hook
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
      console.log("Updating user profile:", updatedProfile);
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

  const {
    meals,
    pendingMeal,
    fetchMealsFromBackend,
    createPendingMeal,
    saveMeal,
    cancelMeal,
    handleDeleteMeal
  } = useMeals();
  
   useEffect(() => {
    fetchUserProfile();
    fetchNutritionNeeds();
    fetchMealsFromBackend(user as User, currentDate);
  }, [currentDate, user]);

  
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
  // ✨ NEW: Show loading screen while determining auth state
  if (isAuthLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 10 }}>Loading...</Text>
        {authError && (
          <Text style={{ color: 'red', marginTop: 10 }}>
            Auth Error: {authError}
          </Text>
        )}
      </View>
    );
  }

  // ✨ NEW: Show login screen if no user (much cleaner logic)
  if (!user) {
    return <LoginScreen onLogin={handleLogin} />;
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
          pendingMeal={pendingMeal}
          createPendingMeal={createPendingMeal}
          saveMeal={(meal) => saveMeal(user as User, meal, currentDate)}
          cancelMeal={cancelMeal}
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
