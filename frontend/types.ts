export interface MealEntry {
  id: string;
  user_id: string;
  description: string;
  assumptions: string;
  calories: number;
  protein?: number;
  carbs?: number;
  fat?: number;
  sugar?: number;
  timestamp?: string;
}

export interface UserProfile {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  weight: string;
  height: string;
}

export interface NutritionNeeds {
  calories: number;
  protein: number;
  fat: number;
  carbs: number;
  sugar: number;
}
