import { useState, useEffect } from 'react';
import api from '../api/axios';
import { MealEntry } from "../types";
import { User } from 'firebase/auth';

// Define the return type for our custom hook
interface UseMealReturn {
    meals: MealEntry[];
    pendingMeal: MealEntry | null;
    fetchMealsFromBackend: (user: User, currentDate: Date) => Promise<void>;
    createPendingMeal: (mealData: MealEntry) => void;
    saveMeal: (user: User, meal: MealEntry, mealDate: Date) => Promise<MealEntry>;
    handleDeleteMeal: (id: string) => Promise<void>;
    cancelMeal: () => void; 
}

export const useMeals = (): UseMealReturn => {
    
    const [meals, setMeals] = useState<MealEntry[]>([]);
    const [pendingMeal, setPendingMeal] = useState<MealEntry | null>(null);

   
    const fetchMealsFromBackend = async (user: User, currentDate: Date) => {
        if (!user?.uid) return;
        try {
        // Use local date - group meals by user's local calendar date
        const dateStr = currentDate.getFullYear() + '-' + 
          String(currentDate.getMonth() + 1).padStart(2, '0') + '-' + 
          String(currentDate.getDate()).padStart(2, '0');
        console.log("Fetching meals for local date:", dateStr);
        const { data } = await api.get(`/meals/${user.uid}`, {
            params: { search_date: dateStr },
        });
        console.log("Fetched meals from backend:", data);
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
    const saveMeal = async (user: User, meal: MealEntry, mealDate: Date) => {
        try {
            // Use local date - save meal for user's local calendar date
            const dateStr = mealDate.getFullYear() + '-' + 
              String(mealDate.getMonth() + 1).padStart(2, '0') + '-' + 
              String(mealDate.getDate()).padStart(2, '0');
            console.log("Saving meal with meal date:", dateStr);
            
            const { data: savedMeal } = await api.post("/meals/", {
                user_id: user?.uid, // Dynamic user ID
                description: meal.description,
                calories: meal.calories,
                protein: meal.protein,
                fiber: meal.fiber,
                carbs: meal.carbs,
                fat: meal.fat,
                sugar: meal.sugar,
                meal_date: dateStr, // Date string in YYYY-MM-DD format
            });

            // Clear conversation state (no thread deletion needed with Responses API)
            setPendingMeal(null);
            setMeals((prevMeals) => [...prevMeals, savedMeal]);
            return savedMeal;
        } 
        catch (error) {
            throw new Error("Failed to save meal");
        }
    };

    const handleDeleteMeal = async (id: string) => {
        try {
            await api.delete(`/meals/${id}`);
            setMeals((prevMeals) => prevMeals.filter((meal) => meal.id !== id));
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
        fetchMealsFromBackend,        
        createPendingMeal,
        saveMeal,
        handleDeleteMeal,
        cancelMeal,
    };
};