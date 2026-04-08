/** Item en lista del histórico de comidas. */

import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import type { Meal } from "../types";

interface MealItemProps {
  meal: Meal;
  onPress: () => void;
}

export function MealItem({ meal, onPress }: MealItemProps) {
  const time = new Date(meal.created_at).toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.info}>
        <Text style={styles.name} numberOfLines={1}>
          {meal.meal_name}
        </Text>
        <Text style={styles.time}>{time}</Text>
      </View>
      <View style={styles.macros}>
        <Text style={styles.calories}>{Math.round(meal.macros.calories)} kcal</Text>
        <Text style={styles.detail}>
          P:{Math.round(meal.macros.protein_g)}g C:{Math.round(meal.macros.carbs_g)}g G:
          {Math.round(meal.macros.fat_g)}g
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#1A1A1A",
    borderRadius: 16,
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  info: {
    flex: 1,
    marginRight: 12,
  },
  name: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 4,
  },
  time: {
    color: "#666666",
    fontSize: 13,
  },
  macros: {
    alignItems: "flex-end",
  },
  calories: {
    color: "#4ADE80",
    fontSize: 16,
    fontWeight: "700",
    marginBottom: 2,
  },
  detail: {
    color: "#999999",
    fontSize: 12,
  },
});
