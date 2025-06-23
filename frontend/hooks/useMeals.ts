import { useState, useEffect } from 'react';
import api from '../api/axios';
import { MealEntry } from "../types";
import { User } from 'firebase/auth';

// Define the return type for our custom hook
interface UseMealReturn {
    pendingMeal: MealEntry | null;
    createPendingMeal: (mealData: MealEntry) => void;
    saveMeal: (meal: MealEntry) => Promise<MealEntry>;
    handleDeleteMeal: (id: string) => Promise<void>;
    cancelMeal: () => void; 
}

export const useMeals = (user: User, currentDate: Date, callbacks?: {onMealSaved?: () => void;}): UseMealReturn => {
    
    const [pendingMeal, setPendingMeal] = useState<MealEntry | null>(null);

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
            callbacks?.onMealSaved?.();
        } catch (error) {
            console.error("Failed to delete meal");
        }
    };
    
    const cancelMeal = () => {
        setPendingMeal(null);
    };

    // Return object with all auth state and functions
    return {
        pendingMeal,        
        createPendingMeal,
        saveMeal,
        handleDeleteMeal,
        cancelMeal,
    };
};