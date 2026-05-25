/** Cálculo cliente-side del bolo de insulina, solo para preview en vivo.
 *
 * Replica `backend/app/services/bolus.py::calculate_bolus`. La fuente de
 * verdad es siempre el servidor: al guardar (PATCH /meals/{id}/bolus) el
 * backend re-calcula con `Decimal` HALF_UP y persiste su resultado.
 * Aquí usamos `Math.round`, que para los valores positivos del bolo se
 * comporta igual en la mayoría de casos. Puede haber drift de ±0.1 U en
 * el borde por imprecisión IEEE-754 — la cifra de verdad es la guardada.
 */

import type {
  BolusCalcResult,
  DiabeticProfile,
  ExerciseLevel,
  TimeSlot,
} from "../types";

const round2 = (v: number) => Math.round(v * 100) / 100;

function iprFor(profile: DiabeticProfile, slot: TimeSlot): number {
  return {
    breakfast: profile.ipr_breakfast,
    lunch: profile.ipr_lunch,
    dinner: profile.ipr_dinner,
  }[slot];
}

function isfFor(profile: DiabeticProfile, slot: TimeSlot): number {
  return {
    breakfast: profile.isf_breakfast,
    lunch: profile.isf_lunch,
    dinner: profile.isf_dinner,
  }[slot];
}

function exerciseFactor(profile: DiabeticProfile, level: ExerciseLevel): number {
  if (level === "moderate") return profile.exercise_moderate_factor;
  if (level === "intense") return profile.exercise_intense_factor;
  return 0;
}

export function calculateBolusLocal(
  carbsG: number,
  glucose: number,
  exercise: ExerciseLevel,
  slot: TimeSlot,
  profile: DiabeticProfile,
): BolusCalcResult {
  const ipr = iprFor(profile, slot);
  const isf = isfFor(profile, slot);

  const rations = Math.round((carbsG / profile.ration_grams) * 10) / 10;
  const bolusCarb = rations * ipr;
  const bolusCorrection = (glucose - profile.target_glucose) / isf;
  const factor = exerciseFactor(profile, exercise);

  const bolusBeforeRound = Math.max(
    0,
    (bolusCarb + bolusCorrection) * (1 + factor),
  );
  const step = profile.bolus_rounding_step;
  const bolusTotal = Math.round(bolusBeforeRound / step) * step;

  return {
    rations,
    bolus_carb: round2(bolusCarb),
    bolus_correction: round2(bolusCorrection),
    exercise_factor: factor,
    bolus_before_round: round2(bolusBeforeRound),
    bolus_total: round2(bolusTotal),
    hypoglycemia_warning: glucose < profile.hypo_threshold,
  };
}
