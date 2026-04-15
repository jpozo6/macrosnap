/** Cliente HTTP para comunicación con el backend. */

import axios from "axios";
import type {
  AnalysisResult,
  DailySummary,
  Meal,
} from "../types";

// Producción: IP del servidor Hetzner (Caddy proxy en puerto 80)
const API_BASE = "http://94.130.228.161/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60s para análisis de imagen
});

export async function analyzeImage(imageUri: string, comment?: string): Promise<AnalysisResult> {
  const formData = new FormData();
  formData.append("image", {
    uri: imageUri,
    type: "image/jpeg",
    name: "meal.jpg",
  } as unknown as Blob);
  if (comment) {
    formData.append("comment", comment);
  }

  const response = await api.post<AnalysisResult>("/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
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

export default api;
