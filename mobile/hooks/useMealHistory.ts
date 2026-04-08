/** Hook para CRUD del histórico de comidas. */

import { useCallback, useState } from "react";
import {
  getMeals,
  deleteMeal as apiDeleteMeal,
  getDailySummary,
} from "../services/api";
import { useMealStore } from "../store/useMealStore";

const PAGE_SIZE = 20;

export function useMealHistory() {
  const {
    meals,
    isLoadingMeals,
    dailySummary,
    setMeals,
    appendMeals,
    removeMeal,
    setLoadingMeals,
    setDailySummary,
  } = useMealStore();

  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchMeals = useCallback(
    async (refresh = false) => {
      setLoadingMeals(true);
      try {
        const newOffset = refresh ? 0 : offset;
        const data = await getMeals({ limit: PAGE_SIZE, offset: newOffset });
        if (refresh) {
          setMeals(data);
          setOffset(PAGE_SIZE);
        } else {
          appendMeals(data);
          setOffset(newOffset + PAGE_SIZE);
        }
        setHasMore(data.length === PAGE_SIZE);
      } finally {
        setLoadingMeals(false);
      }
    },
    [offset, setMeals, appendMeals, setLoadingMeals]
  );

  const fetchMore = useCallback(() => {
    if (!isLoadingMeals && hasMore) {
      fetchMeals(false);
    }
  }, [isLoadingMeals, hasMore, fetchMeals]);

  const refresh = useCallback(() => fetchMeals(true), [fetchMeals]);

  const deleteMeal = useCallback(
    async (id: number) => {
      await apiDeleteMeal(id);
      removeMeal(id);
    },
    [removeMeal]
  );

  const fetchDailySummary = useCallback(
    async (date: string) => {
      const summary = await getDailySummary(date);
      setDailySummary(summary);
    },
    [setDailySummary]
  );

  return {
    meals,
    isLoading: isLoadingMeals,
    hasMore,
    fetchMeals: refresh,
    fetchMore,
    deleteMeal,
    dailySummary,
    fetchDailySummary,
  };
}
