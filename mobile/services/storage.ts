/** Helpers para AsyncStorage. */

import AsyncStorage from "@react-native-async-storage/async-storage";
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
  const stored = await AsyncStorage.getItem(KEYS.MACRO_GOALS);
  return stored ? JSON.parse(stored) : DEFAULT_GOALS;
}

export async function saveMacroGoals(goals: MacroGoals): Promise<void> {
  await AsyncStorage.setItem(KEYS.MACRO_GOALS, JSON.stringify(goals));
}
