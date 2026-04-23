/** Tipos compartidos de MacroSnap */

export interface MacroNutrients {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  fiber_g: number;
}

export interface FoodItem {
  name: string;
  confidence: number;
  amount?: number;
  unit?: string;
}

export interface AnalysisResult {
  meal_id: number;
  meal_name: string;
  macros: MacroNutrients;
  foods: FoodItem[];
}

export interface Meal {
  id: number;
  meal_name: string;
  macros: MacroNutrients;
  foods: FoodItem[];
  image_base64?: string;
  created_at: string;
}

export interface DailySummary {
  date: string;
  total_meals: number;
  macros: MacroNutrients;
}

export interface MacroGoals {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export type AnalysisStatus = "idle" | "loading" | "success" | "error";

export interface User {
  id: number;
  email: string;
  is_verified: boolean;
  created_at: string;
}

export interface AuthSession {
  token: string;
  user: User;
}
