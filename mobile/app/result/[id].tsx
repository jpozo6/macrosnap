/** Detalle de resultado de análisis de comida. */

import { Ionicons } from "@expo/vector-icons";
import { router, useFocusEffect, useLocalSearchParams } from "expo-router";
import { useCallback, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { MacroCard } from "../../components/MacroCard";
import { getMeal } from "../../services/api";
import { TIME_SLOT_LABELS } from "../../services/timeSlot";
import { useDiabeticStore } from "../../store/useDiabeticStore";
import { useMealStore } from "../../store/useMealStore";
import type { ExerciseLevel, Meal } from "../../types";

const EXERCISE_LABEL: Record<ExerciseLevel, string> = {
  none: "Sin ejercicio",
  moderate: "Ejercicio moderado",
  intense: "Ejercicio intenso",
};

export default function ResultScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const goals = useMealStore((s) => s.goals);
  const profile = useDiabeticStore((s) => s.profile);
  const [meal, setMeal] = useState<Meal | null>(null);
  const [loading, setLoading] = useState(true);

  // Recargamos al volver de la pantalla de bolo para reflejar el cambio.
  useFocusEffect(
    useCallback(() => {
      if (!id) return;
      setLoading(true);
      getMeal(Number(id))
        .then(setMeal)
        .finally(() => setLoading(false));
    }, [id]),
  );

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

      <MacroCard macros={meal.macros} goals={goals} rationGrams={profile?.ration_grams} />

      {profile ? <BolusSection meal={meal} /> : null}

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

function BolusSection({ meal }: { meal: Meal }) {
  if (!meal.bolus) {
    return (
      <View style={styles.bolusCtaWrap}>
        <TouchableOpacity
          style={styles.bolusCta}
          onPress={() => router.push(`/bolus/${meal.id}`)}
        >
          <Ionicons name="medkit" size={20} color="#0F0F0F" />
          <Text style={styles.bolusCtaText}>Calcular bolo de insulina</Text>
        </TouchableOpacity>
      </View>
    );
  }
  const b = meal.bolus;
  return (
    <View style={styles.bolusCard}>
      <View style={styles.bolusHeader}>
        <Text style={styles.bolusTitle}>Bolo administrado</Text>
        <TouchableOpacity onPress={() => router.push(`/bolus/${meal.id}`)}>
          <Text style={styles.bolusEditLink}>Editar</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.bolusTotalRow}>
        <Text style={styles.bolusTotalValue}>{b.bolus_total_units.toFixed(1)}</Text>
        <Text style={styles.bolusTotalUnit}>U</Text>
        {b.bolus_total_units !== b.bolus_suggested_units && (
          <Text style={styles.bolusVsSuggested}>
            (sugerido {b.bolus_suggested_units.toFixed(1)} U)
          </Text>
        )}
      </View>

      <View style={styles.bolusGrid}>
        <BolusGridItem label="Raciones HC" value={`${b.rations_hc}`} />
        <BolusGridItem label="Glucemia" value={`${b.glucose_mg_dl} mg/dL`} />
        <BolusGridItem label="Franja" value={TIME_SLOT_LABELS[b.slot]} />
        <BolusGridItem label="Ejercicio" value={EXERCISE_LABEL[b.exercise_level]} />
      </View>
    </View>
  );
}

function BolusGridItem({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.bolusGridItem}>
      <Text style={styles.bolusGridLabel}>{label}</Text>
      <Text style={styles.bolusGridValue}>{value}</Text>
    </View>
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
  // ===== Bolo =====
  bolusCtaWrap: { marginTop: 20 },
  bolusCta: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  bolusCtaText: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
  bolusCard: {
    backgroundColor: "#1A1A1A",
    borderRadius: 16,
    padding: 16,
    marginTop: 20,
  },
  bolusHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  bolusTitle: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
  bolusEditLink: { color: "#4ADE80", fontSize: 14, fontWeight: "600" },
  bolusTotalRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 6,
    marginBottom: 12,
  },
  bolusTotalValue: { color: "#4ADE80", fontSize: 36, fontWeight: "800" },
  bolusTotalUnit: { color: "#4ADE80", fontSize: 18, fontWeight: "700" },
  bolusVsSuggested: { color: "#777", fontSize: 12, marginLeft: 8 },
  bolusGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  bolusGridItem: {
    flexBasis: "48%",
    flexGrow: 1,
    backgroundColor: "#141414",
    borderRadius: 10,
    padding: 10,
  },
  bolusGridLabel: { color: "#777", fontSize: 11, marginBottom: 2 },
  bolusGridValue: { color: "#FFF", fontSize: 14, fontWeight: "600" },
});
