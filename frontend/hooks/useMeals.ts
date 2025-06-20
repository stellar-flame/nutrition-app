import { useState, useEffect } from 'react';
import api from '../api/axios';
import { MealEntry } from "../types";
import { User } from 'firebase/auth';

// Define the return type for our custom hook
interface UseMealReturn {
    meals: MealEntry[];
    pendingMeal: MealEntry | null;
    createPendingMeal: (mealData: MealEntry) => void;
    saveMeal: (meal: MealEntry) => Promise<MealEntry>;
    handleDeleteMeal: (id: string) => Promise<void>;
    cancelMeal: () => void; 
}

export const useMeals = (user: User, currentDate: Date, callbacks?: {onMealSaved?: () => void;
    onMealCancelled?: () => void; }): UseMealReturn => {
    
    const [meals, setMeals] = useState<MealEntry[]>([]);
    const [pendingMeal, setPendingMeal] = useState<MealEntry | null>(null);

    useEffect(() => {
        fetchMealsFromBackend();
    }, [currentDate, user]);
      
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

    const createPendingMeal = (mealData: MealEntry) => {
       setPendingMeal(mealData);
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

            // Clear conversation state (no thread deletion needed with Responses API)
            setPendingMeal(null);
            callbacks?.onMealSaved?.();
            return savedMeal;
        } 
        catch (error) {
            throw new Error("Failed to save meal");
        }
    };

    
    const handleDeleteMeal = async (id: string) => {
        try {
            await api.delete(`/meals/${id}`);
            setMeals((prev) => prev.filter((meal) => meal.id !== id));
        } catch (error) {
            console.error("Failed to delete meal");
        }
    };
    
    const cancelMeal = () => {
        setPendingMeal(null);
    };

    // Return object with all auth state and functions
    return {
        meals,
        pendingMeal,        
        createPendingMeal,
        saveMeal,
        handleDeleteMeal,
        cancelMeal,
    };
};