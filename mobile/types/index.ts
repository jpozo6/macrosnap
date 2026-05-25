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

export interface BolusData {
  glucose_mg_dl: number;
  exercise_level: ExerciseLevel;
  slot: TimeSlot;
  rations_hc: number;
  bolus_carb_units: number;
  bolus_correction_units: number;
  bolus_suggested_units: number;
  bolus_total_units: number;
}

export interface Meal {
  id: number;
  meal_name: string;
  macros: MacroNutrients;
  foods: FoodItem[];
  image_base64?: string;
  created_at: string;
  bolus?: BolusData | null;
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

// ===== Diabetes / bolo de insulina =====

export type TimeSlot = "breakfast" | "lunch" | "dinner";
export type ExerciseLevel = "none" | "moderate" | "intense";
export type BolusRoundingStep = 0.1 | 0.5 | 1.0;

/** Perfil diabético del usuario (1:1 con la cuenta). */
export interface DiabeticProfile {
  id: number;
  ration_grams: number;
  target_glucose: number;
  hypo_threshold: number;
  bolus_rounding_step: BolusRoundingStep;
  exercise_moderate_factor: number; // fracción negativa, p. ej. -0.20
  exercise_intense_factor: number;
  ipr_breakfast: number;
  ipr_lunch: number;
  ipr_dinner: number;
  isf_breakfast: number;
  isf_lunch: number;
  isf_dinner: number;
  created_at: string;
  updated_at: string;
}

/** Datos enviados al backend para crear o actualizar el perfil. */
export type DiabeticProfileUpsert = Omit<
  DiabeticProfile,
  "id" | "created_at" | "updated_at"
>;

export interface BolusCalcRequest {
  carbs_g: number;
  glucose: number;
  exercise: ExerciseLevel;
  slot: TimeSlot;
}

export interface BolusCalcResult {
  rations: number;
  bolus_carb: number;
  bolus_correction: number;
  exercise_factor: number;
  bolus_before_round: number;
  bolus_total: number;
  hypoglycemia_warning: boolean;
}
