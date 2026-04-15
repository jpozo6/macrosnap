/** Helpers para persistencia de datos. */

import { Platform } from "react-native";
import type { MacroGoals } from "../types";

const KEYS = {
  MACRO_GOALS: "macrosnap_goals",
} as const;

const DEFAULT_GOALS: MacroGoals = {
  calories: 2000,
  protein_g: 150,
  carbs_g: 250,
  fat_g: 65,
};

export async function getMacroGoals(): Promise<MacroGoals> {
  if (Platform.OS === "web") {
    const stored = localStorage.getItem(KEYS.MACRO_GOALS);
    return stored ? JSON.parse(stored) : DEFAULT_GOALS;
  }
  const AsyncStorage = (await import("@react-native-async-storage/async-storage")).default;
  const stored = await AsyncStorage.getItem(KEYS.MACRO_GOALS);
  return stored ? JSON.parse(stored) : DEFAULT_GOALS;
}

export async function saveMacroGoals(goals: MacroGoals): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.setItem(KEYS.MACRO_GOALS, JSON.stringify(goals));
    return;
  }
  const AsyncStorage = (await import("@react-native-async-storage/async-storage")).default;
  await AsyncStorage.setItem(KEYS.MACRO_GOALS, JSON.stringify(goals));
}
