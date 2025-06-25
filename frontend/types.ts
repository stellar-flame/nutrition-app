export interface MealEntry {
  id: string;
  user_id: string;
  description: string;
  assumptions: string;
  calories: number;
  protein?: number;
  fiber?: number;
  carbs?: number;
  fat?: number;
  sugar?: number;
  date?: string;
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
  fiber: number;
  fat: number;
  carbs: number;
  sugar: number;
}
