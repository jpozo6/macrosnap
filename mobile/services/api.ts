/** Cliente HTTP para comunicación con el backend. */

import axios from "axios";
import { Platform } from "react-native";
import type {
  AnalysisResult,
  DailySummary,
  ExerciseLevel,
  Meal,
  TimeSlot,
} from "../types";

// Producción: IP del servidor Hetzner (Caddy proxy en puerto 80)
const API_BASE = "http://94.130.228.161/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60s para análisis de imagen
});

// Token provider inyectable desde el auth store. Evita import circular.
let tokenProvider: () => string | null = () => null;
let onUnauthorized: (() => void) | null = null;

export function configureAuth(opts: {
  getToken: () => string | null;
  onUnauthorized?: () => void;
}): void {
  tokenProvider = opts.getToken;
  onUnauthorized = opts.onUnauthorized ?? null;
}

api.interceptors.request.use((config) => {
  const token = tokenProvider();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Solo tratamos como sesión expirada si había token en la request.
    const hadAuth = !!error?.config?.headers?.Authorization;
    const status = error?.response?.status;
    if (hadAuth && (status === 401 || status === 403) && onUnauthorized) {
      onUnauthorized();
    }
    return Promise.reject(error);
  },
);

export async function analyzeImage(imageUri: string, comment?: string): Promise<AnalysisResult> {
  const formData = new FormData();

  if (Platform.OS === "web") {
    // En web, imageUri es un blob URL — fetch para obtener el File
    const response = await fetch(imageUri);
    const blob = await response.blob();
    formData.append("image", blob, "meal.jpg");
  } else {
    formData.append("image", {
      uri: imageUri,
      type: "image/jpeg",
      name: "meal.jpg",
    } as unknown as Blob);
  }

  if (comment) {
    formData.append("comment", comment);
  }

  const res = await api.post<AnalysisResult>("/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function getMeals(params?: {
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
}): Promise<Meal[]> {
  const response = await api.get<Meal[]>("/meals", { params });
  return response.data;
}

export async function getMeal(id: number): Promise<Meal> {
  const response = await api.get<Meal>(`/meals/${id}`);
  return response.data;
}

export async function deleteMeal(id: number): Promise<void> {
  await api.delete(`/meals/${id}`);
}

export async function getDailySummary(date: string): Promise<DailySummary> {
  const response = await api.get<DailySummary>("/meals/summary/daily", {
    params: { date },
  });
  return response.data;
}

export interface SetMealBolusPayload {
  glucose: number;
  exercise: ExerciseLevel;
  slot: TimeSlot;
  bolus_chosen_units: number;
}

/** Registra el bolo de insulina en una comida ya analizada.
 * El backend recalcula el desglose con el perfil vigente; solo se persiste
 * tal cual el `bolus_chosen_units` que decida el usuario. */
export async function setMealBolus(
  mealId: number,
  payload: SetMealBolusPayload,
): Promise<Meal> {
  const res = await api.patch<Meal>(`/meals/${mealId}/bolus`, payload);
  return res.data;
}

export default api;
