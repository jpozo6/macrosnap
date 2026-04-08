/** Resumen diario de macros fijo arriba del histórico. */

import { View, Text, StyleSheet } from "react-native";
import type { DailySummary as DailySummaryType, MacroGoals } from "../types";

interface DailySummaryProps {
  summary: DailySummaryType | null;
  goals: MacroGoals;
}

export function DailySummary({ summary, goals }: DailySummaryProps) {
  if (!summary) return null;

  const items = [
    { label: "Kcal", value: summary.macros.calories, goal: goals.calories, color: "#4ADE80" },
    { label: "Prot", value: summary.macros.protein_g, goal: goals.protein_g, color: "#4ADE80" },
    { label: "Carbs", value: summary.macros.carbs_g, goal: goals.carbs_g, color: "#60A5FA" },
    { label: "Grasa", value: summary.macros.fat_g, goal: goals.fat_g, color: "#FBBF24" },
  ];

  return (
    <View style={styles.container}>
      <Text style={styles.title}>
        Hoy — {summary.total_meals} comida{summary.total_meals !== 1 ? "s" : ""}
      </Text>
      <View style={styles.row}>
        {items.map((item) => (
          <View key={item.label} style={styles.item}>
            <Text style={[styles.value, { color: item.color }]}>
              {Math.round(item.value)}
            </Text>
            <Text style={styles.label}>
              / {item.goal} {item.label}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1A1A1A",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
  },
  title: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
    marginBottom: 12,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  item: {
    alignItems: "center",
  },
  value: {
    fontSize: 18,
    fontWeight: "700",
  },
  label: {
    color: "#666666",
    fontSize: 11,
    marginTop: 2,
  },
});
