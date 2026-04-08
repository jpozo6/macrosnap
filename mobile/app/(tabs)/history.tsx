/** Pantalla de histórico de comidas agrupado por fecha. */

import { useEffect, useMemo, useCallback } from "react";
import {
  View,
  Text,
  SectionList,
  StyleSheet,
  RefreshControl,
} from "react-native";
import { useRouter } from "expo-router";
import { useMealHistory } from "../../hooks/useMealHistory";
import { useMealStore } from "../../store/useMealStore";
import { MealItem } from "../../components/MealItem";
import { DailySummary } from "../../components/DailySummary";
import type { Meal } from "../../types";

export default function HistoryScreen() {
  const router = useRouter();
  const goals = useMealStore((s) => s.goals);
  const {
    meals,
    isLoading,
    fetchMeals,
    fetchMore,
    dailySummary,
    fetchDailySummary,
  } = useMealHistory();

  useEffect(() => {
    fetchMeals();
    const today = new Date().toISOString().split("T")[0];
    fetchDailySummary(today);
  }, []);

  const sections = useMemo(() => {
    const grouped: Record<string, Meal[]> = {};
    for (const meal of meals) {
      const date = new Date(meal.created_at).toLocaleDateString("es", {
        weekday: "long",
        day: "numeric",
        month: "long",
      });
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(meal);
    }
    return Object.entries(grouped).map(([title, data]) => ({ title, data }));
  }, [meals]);

  const handleMealPress = useCallback(
    (id: number) => {
      router.push(`/result/${id}`);
    },
    [router]
  );

  return (
    <View style={styles.container}>
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <MealItem meal={item} onPress={() => handleMealPress(item.id)} />
        )}
        renderSectionHeader={({ section: { title } }) => (
          <Text style={styles.sectionHeader}>{title}</Text>
        )}
        ListHeaderComponent={<DailySummary summary={dailySummary} goals={goals} />}
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>
                No hay comidas registradas
              </Text>
              <Text style={styles.emptySubtext}>
                Saca una foto de tu comida para empezar
              </Text>
            </View>
          ) : null
        }
        onEndReached={fetchMore}
        onEndReachedThreshold={0.5}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={fetchMeals}
            tintColor="#4ADE80"
          />
        }
        contentContainerStyle={styles.content}
        stickySectionHeadersEnabled={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F0F0F",
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  sectionHeader: {
    color: "#999999",
    fontSize: 13,
    fontWeight: "600",
    textTransform: "capitalize",
    marginTop: 16,
    marginBottom: 8,
  },
  empty: {
    alignItems: "center",
    paddingTop: 60,
  },
  emptyText: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 8,
  },
  emptySubtext: {
    color: "#666666",
    fontSize: 14,
  },
});
