/** Detalle de resultado de análisis de comida. */

import { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useLocalSearchParams } from "expo-router";
import { getMeal } from "../../services/api";
import { MacroCard } from "../../components/MacroCard";
import { useMealStore } from "../../store/useMealStore";
import type { Meal } from "../../types";

export default function ResultScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const goals = useMealStore((s) => s.goals);
  const [meal, setMeal] = useState<Meal | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      getMeal(Number(id))
        .then(setMeal)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4ADE80" />
      </View>
    );
  }

  if (!meal) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Comida no encontrada</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.mealName}>{meal.meal_name}</Text>
      <Text style={styles.date}>
        {new Date(meal.created_at).toLocaleDateString("es", {
          weekday: "long",
          day: "numeric",
          month: "long",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </Text>

      <MacroCard macros={meal.macros} goals={goals} />

      <View style={styles.foodsSection}>
        <Text style={styles.foodsTitle}>Alimentos identificados</Text>
        {meal.foods.map((food, index) => (
          <View key={index} style={styles.foodItem}>
            <View style={styles.foodInfo}>
              <Text style={styles.foodName}>{food.name}</Text>
              {food.amount && (
                <Text style={styles.foodPortion}>
                  {food.amount} {food.unit}
                </Text>
              )}
            </View>
            <Text style={styles.foodConfidence}>
              {Math.round((food.confidence ?? 0) * 100)}%
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F0F0F",
  },
  content: {
    padding: 20,
  },
  center: {
    flex: 1,
    backgroundColor: "#0F0F0F",
    justifyContent: "center",
    alignItems: "center",
  },
  mealName: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "700",
    marginBottom: 4,
  },
  date: {
    color: "#666666",
    fontSize: 14,
    marginBottom: 24,
  },
  foodsSection: {
    marginTop: 24,
  },
  foodsTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 12,
  },
  foodItem: {
    backgroundColor: "#1A1A1A",
    borderRadius: 12,
    padding: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  foodInfo: {
    flex: 1,
  },
  foodName: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "500",
  },
  foodPortion: {
    color: "#999999",
    fontSize: 13,
    marginTop: 2,
  },
  foodConfidence: {
    color: "#4ADE80",
    fontSize: 14,
    fontWeight: "600",
  },
  errorText: {
    color: "#999999",
    fontSize: 16,
  },
});
