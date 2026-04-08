/** Zustand store para estado global de comidas. */

import { create } from "zustand";
import type {
  AnalysisResult,
  AnalysisStatus,
  DailySummary,
  MacroGoals,
  Meal,
} from "../types";

interface MealStore {
  // Estado de análisis
  analysisStatus: AnalysisStatus;
  analysisResult: AnalysisResult | null;
  analysisError: string | null;

  // Histórico
  meals: Meal[];
  isLoadingMeals: boolean;

  // Resumen diario
  dailySummary: DailySummary | null;

  // Objetivos
  goals: MacroGoals;

  // Acciones de análisis
  setAnalysisLoading: () => void;
  setAnalysisSuccess: (result: AnalysisResult) => void;
  setAnalysisError: (error: string) => void;
  resetAnalysis: () => void;

  // Acciones de histórico
  setMeals: (meals: Meal[]) => void;
  appendMeals: (meals: Meal[]) => void;
  removeMeal: (id: number) => void;
  setLoadingMeals: (loading: boolean) => void;

  // Acciones de resumen
  setDailySummary: (summary: DailySummary | null) => void;

  // Acciones de objetivos
  setGoals: (goals: MacroGoals) => void;
}

export const useMealStore = create<MealStore>((set) => ({
  analysisStatus: "idle",
  analysisResult: null,
  analysisError: null,
  meals: [],
  isLoadingMeals: false,
  dailySummary: null,
  goals: { calories: 2000, protein_g: 150, carbs_g: 250, fat_g: 65 },

  setAnalysisLoading: () =>
    set({ analysisStatus: "loading", analysisResult: null, analysisError: null }),
  setAnalysisSuccess: (result) =>
    set({ analysisStatus: "success", analysisResult: result }),
  setAnalysisError: (error) =>
    set({ analysisStatus: "error", analysisError: error }),
  resetAnalysis: () =>
    set({ analysisStatus: "idle", analysisResult: null, analysisError: null }),

  setMeals: (meals) => set({ meals }),
  appendMeals: (newMeals) =>
    set((state) => ({ meals: [...state.meals, ...newMeals] })),
  removeMeal: (id) =>
    set((state) => ({ meals: state.meals.filter((m) => m.id !== id) })),
  setLoadingMeals: (loading) => set({ isLoadingMeals: loading }),

  setDailySummary: (summary) => set({ dailySummary: summary }),
  setGoals: (goals) => set({ goals }),
}));
