/** Tarjeta con macronutrientes: calorías en anillo, barras para P/C/G. */

import { View, Text, StyleSheet } from "react-native";
import type { MacroNutrients, MacroGoals } from "../types";
import { NutrientBar } from "./NutrientBar";

interface MacroCardProps {
  macros: MacroNutrients;
  goals?: MacroGoals;
}

export function MacroCard({ macros, goals }: MacroCardProps) {
  const defaultGoals: MacroGoals = goals ?? {
    calories: 2000,
    protein_g: 150,
    carbs_g: 250,
    fat_g: 65,
  };

  const calPercent = Math.min(macros.calories / defaultGoals.calories, 1);

  return (
    <View style={styles.card}>
      {/* Calorías circular */}
      <View style={styles.calorieSection}>
        <View style={styles.calorieRing}>
          <Text style={styles.calorieValue}>{Math.round(macros.calories)}</Text>
          <Text style={styles.calorieLabel}>kcal</Text>
        </View>
        <Text style={styles.calorieGoal}>
          de {defaultGoals.calories} kcal ({Math.round(calPercent * 100)}%)
        </Text>
      </View>

      {/* Barras de macros */}
      <View style={styles.barsSection}>
        <NutrientBar
          label="Proteína"
          value={macros.protein_g}
          goal={defaultGoals.protein_g}
          unit="g"
          color="#4ADE80"
        />
        <NutrientBar
          label="Carbohidratos"
          value={macros.carbs_g}
          goal={defaultGoals.carbs_g}
          unit="g"
          color="#60A5FA"
        />
        <NutrientBar
          label="Grasa"
          value={macros.fat_g}
          goal={defaultGoals.fat_g}
          unit="g"
          color="#FBBF24"
        />
        {macros.fiber_g > 0 && (
          <NutrientBar
            label="Fibra"
            value={macros.fiber_g}
            goal={30}
            unit="g"
            color="#A78BFA"
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#1A1A1A",
    borderRadius: 16,
    padding: 20,
  },
  calorieSection: {
    alignItems: "center",
    marginBottom: 20,
  },
  calorieRing: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 4,
    borderColor: "#4ADE80",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 8,
  },
  calorieValue: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "700",
  },
  calorieLabel: {
    color: "#999999",
    fontSize: 12,
  },
  calorieGoal: {
    color: "#666666",
    fontSize: 13,
  },
  barsSection: {
    gap: 4,
  },
});
