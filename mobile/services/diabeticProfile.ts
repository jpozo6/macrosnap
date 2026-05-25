/** Cliente HTTP para los endpoints del perfil diabético. */

import api from "./api";
import type {
  BolusCalcRequest,
  BolusCalcResult,
  DiabeticProfile,
  DiabeticProfileUpsert,
} from "../types";

const BASE = "/diabetic-profile";

/** Devuelve el perfil o `null` si el usuario no lo ha configurado (404). */
export async function getProfile(): Promise<DiabeticProfile | null> {
  try {
    const res = await api.get<DiabeticProfile>(BASE);
    return res.data;
  } catch (err: any) {
    if (err?.response?.status === 404) return null;
    throw err;
  }
}

/** Crea o actualiza (upsert) el perfil del usuario. */
export async function upsertProfile(
  data: DiabeticProfileUpsert,
): Promise<DiabeticProfile> {
  const res = await api.put<DiabeticProfile>(BASE, data);
  return res.data;
}

/** Borra el perfil — equivalente a desactivar el modo diabético. */
export async function deleteProfile(): Promise<void> {
  await api.delete(BASE);
}

export async function calculateBolus(
  payload: BolusCalcRequest,
): Promise<BolusCalcResult> {
  const res = await api.post<BolusCalcResult>(`${BASE}/calculate-bolus`, payload);
  return res.data;
}
