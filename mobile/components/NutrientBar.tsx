/** Barra de progreso horizontal para un nutriente. */

import { View, Text, StyleSheet } from "react-native";

interface NutrientBarProps {
  label: string;
  value: number;
  goal: number;
  unit: string;
  color: string;
}

export function NutrientBar({ label, value, goal, unit, color }: NutrientBarProps) {
  const progress = Math.min(value / goal, 1);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.label}>{label}</Text>
        <Text style={styles.value}>
          {Math.round(value)}{unit} / {goal}{unit}
        </Text>
      </View>
      <View style={styles.trackOuter}>
        <View
          style={[styles.trackFill, { width: `${progress * 100}%`, backgroundColor: color }]}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  label: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "500",
  },
  value: {
    color: "#999999",
    fontSize: 13,
  },
  trackOuter: {
    height: 8,
    borderRadius: 4,
    backgroundColor: "#2A2A2A",
    overflow: "hidden",
  },
  trackFill: {
    height: "100%",
    borderRadius: 4,
  },
});
