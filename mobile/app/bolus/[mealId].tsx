/** Pantalla del cálculo del bolo de insulina para una comida concreta.
 *
 * Flujo:
 *   1. Carga el meal (para conocer `carbs_g`) y el perfil del store.
 *   2. Pre-rellena `glucose` vacío, `exercise=none`, `slot=currentSlot()`.
 *      Si la comida ya tenía bolo registrado, hidratamos sus valores.
 *   3. Cualquier cambio en la entrada recalcula el preview cliente-side.
 *      Se muestra el desglose y la cifra final editable.
 *   4. Aviso de hipoglucemia (NO bloquea — el usuario decide).
 *   5. Guardar -> PATCH al backend (que recalcula y persiste).
 */

import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { getMeal, setMealBolus } from "../../services/api";
import { showAlert } from "../../services/alert";
import { calculateBolusLocal } from "../../services/bolusCalc";
import { currentSlot, TIME_SLOT_LABELS } from "../../services/timeSlot";
import { useDiabeticStore } from "../../store/useDiabeticStore";
import type {
  BolusCalcResult,
  ExerciseLevel,
  Meal,
  TimeSlot,
} from "../../types";

const EXERCISE_OPTIONS: { value: ExerciseLevel; label: string }[] = [
  { value: "none", label: "Ninguno" },
  { value: "moderate", label: "Moderado" },
  { value: "intense", label: "Intenso" },
];

const SLOT_OPTIONS: { value: TimeSlot; label: string }[] = [
  { value: "breakfast", label: TIME_SLOT_LABELS.breakfast },
  { value: "lunch", label: TIME_SLOT_LABELS.lunch },
  { value: "dinner", label: TIME_SLOT_LABELS.dinner },
];

export default function BolusScreen() {
  const { mealId } = useLocalSearchParams<{ mealId: string }>();
  const profile = useDiabeticStore((s) => s.profile);

  const [meal, setMeal] = useState<Meal | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [glucose, setGlucose] = useState<string>("");
  const [exercise, setExercise] = useState<ExerciseLevel>("none");
  const [slot, setSlot] = useState<TimeSlot>(currentSlot());
  // Si el usuario tocó manualmente la cifra final, no la sobrescribimos
  // al recalcular el preview.
  const [chosenBolus, setChosenBolus] = useState<string>("");
  const [chosenIsTouched, setChosenIsTouched] = useState(false);

  useEffect(() => {
    if (!mealId) return;
    getMeal(Number(mealId))
      .then((m) => {
        setMeal(m);
        if (m.bolus) {
          // Re-edición de un bolo ya guardado.
          setGlucose(String(m.bolus.glucose_mg_dl));
          setExercise(m.bolus.exercise_level);
          setSlot(m.bolus.slot);
          setChosenBolus(String(m.bolus.bolus_total_units));
          setChosenIsTouched(true);
        }
      })
      .finally(() => setLoading(false));
  }, [mealId]);

  const preview: BolusCalcResult | null = useMemo(() => {
    if (!profile || !meal) return null;
    const g = Number(glucose.replace(",", "."));
    if (!Number.isFinite(g) || g <= 0) return null;
    return calculateBolusLocal(meal.macros.carbs_g, g, exercise, slot, profile);
  }, [profile, meal, glucose, exercise, slot]);

  // Cuando el preview cambia y el usuario aún no ha tocado el campo final,
  // proponemos el sugerido como valor por defecto editable.
  useEffect(() => {
    if (preview && !chosenIsTouched) {
      setChosenBolus(String(preview.bolus_total));
    }
  }, [preview, chosenIsTouched]);

  const handleSave = async () => {
    if (!meal) return;
    const g = Number(glucose.replace(",", "."));
    if (!Number.isFinite(g) || g < 20 || g > 600) {
      showAlert("Glucemia inválida", "Introduce un valor entre 20 y 600 mg/dL.");
      return;
    }
    const chosen = Number(chosenBolus.replace(",", "."));
    if (!Number.isFinite(chosen) || chosen < 0 || chosen > 50) {
      showAlert("Bolo inválido", "El bolo final debe estar entre 0 y 50 U.");
      return;
    }
    setSaving(true);
    try {
      await setMealBolus(meal.id, {
        glucose: g,
        exercise,
        slot,
        bolus_chosen_units: chosen,
      });
      router.replace(`/result/${meal.id}`);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ?? err?.message ?? "No se pudo guardar el bolo.";
      showAlert("Error", String(detail));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color="#4ADE80" />
      </View>
    );
  }

  if (!meal) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorTxt}>Comida no encontrada.</Text>
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.center}>
        <Ionicons name="medkit-outline" size={48} color="#FBBF24" />
        <Text style={styles.errorTxt}>
          Configura tu perfil diabético en la pestaña Diabetes antes de calcular
          el bolo.
        </Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.mealTitle} numberOfLines={1}>
          {meal.meal_name}
        </Text>
        <Text style={styles.mealSubtitle}>
          {Math.round(meal.macros.carbs_g)} g de hidratos · objetivo {profile.target_glucose} mg/dL
        </Text>

        <SectionTitle>Glucemia actual</SectionTitle>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={glucose}
            onChangeText={(v) => {
              setGlucose(v);
              setChosenIsTouched(false);
            }}
            placeholder="ej. 140"
            placeholderTextColor="#555"
            keyboardType="number-pad"
            autoFocus
          />
          <Text style={styles.unit}>mg/dL</Text>
        </View>

        {preview?.hypoglycemia_warning && (
          <View style={styles.warningBox}>
            <Ionicons name="warning" size={18} color="#FBBF24" />
            <Text style={styles.warningTxt}>
              Hipoglucemia ({glucose} mg/dL &lt; {profile.hypo_threshold}). Considera
              tomar HC rápidos antes de pincharte. La app sigue calculando.
            </Text>
          </View>
        )}

        <SectionTitle>Ejercicio reciente o previsto</SectionTitle>
        <SegmentedRow
          options={EXERCISE_OPTIONS}
          value={exercise}
          onChange={(v) => {
            setExercise(v);
            setChosenIsTouched(false);
          }}
        />

        <SectionTitle>Franja</SectionTitle>
        <SegmentedRow
          options={SLOT_OPTIONS}
          value={slot}
          onChange={(v) => {
            setSlot(v);
            setChosenIsTouched(false);
          }}
        />

        {preview && (
          <View style={styles.breakdownCard}>
            <BreakdownRow
              label={`Raciones de HC (${profile.ration_grams} g/ración)`}
              value={`${preview.rations}`}
            />
            <BreakdownRow
              label={`Bolo por HC (× ${slotIpr(profile, slot)} U)`}
              value={`${preview.bolus_carb.toFixed(2)} U`}
            />
            <BreakdownRow
              label={`Corrección (objetivo ${profile.target_glucose} · sens. ${slotIsf(profile, slot)})`}
              value={`${preview.bolus_correction >= 0 ? "+" : ""}${preview.bolus_correction.toFixed(2)} U`}
              tint={preview.bolus_correction < 0 ? "#FBBF24" : undefined}
            />
            {preview.exercise_factor !== 0 && (
              <BreakdownRow
                label="Ajuste por ejercicio"
                value={`${Math.round(preview.exercise_factor * 100)} %`}
                tint="#60A5FA"
              />
            )}
            <View style={styles.suggestedRow}>
              <Text style={styles.suggestedLabel}>Bolo sugerido</Text>
              <Text style={styles.suggestedValue}>
                {preview.bolus_total.toFixed(1)} U
              </Text>
            </View>
          </View>
        )}

        <SectionTitle>Bolo final a administrar</SectionTitle>
        <Text style={styles.help}>
          Edita la cifra si tu endocrino te ha indicado otra cosa o si decides
          ajustarla manualmente.
        </Text>
        <View style={styles.inputRow}>
          <TextInput
            style={[styles.input, styles.inputLarge]}
            value={chosenBolus}
            onChangeText={(v) => {
              setChosenBolus(v);
              setChosenIsTouched(true);
            }}
            placeholder={preview ? String(preview.bolus_total) : "0"}
            placeholderTextColor="#555"
            keyboardType="decimal-pad"
          />
          <Text style={styles.unit}>U</Text>
        </View>

        <TouchableOpacity
          style={[styles.primaryBtn, saving && styles.btnDisabled]}
          onPress={handleSave}
          disabled={saving}
        >
          <Text style={styles.primaryBtnTxt}>
            {saving ? "Guardando..." : meal.bolus ? "Actualizar bolo" : "Guardar bolo"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondaryBtn}
          onPress={() => router.back()}
          disabled={saving}
        >
          <Text style={styles.secondaryTxt}>Cancelar</Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ===== Helpers de UI =====

function slotIpr(
  profile: NonNullable<ReturnType<typeof useDiabeticStore.getState>["profile"]>,
  slot: TimeSlot,
): number {
  return {
    breakfast: profile.ipr_breakfast,
    lunch: profile.ipr_lunch,
    dinner: profile.ipr_dinner,
  }[slot];
}

function slotIsf(
  profile: NonNullable<ReturnType<typeof useDiabeticStore.getState>["profile"]>,
  slot: TimeSlot,
): number {
  return {
    breakfast: profile.isf_breakfast,
    lunch: profile.isf_lunch,
    dinner: profile.isf_dinner,
  }[slot];
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.section}>{children}</Text>;
}

function SegmentedRow<V extends string>({
  options,
  value,
  onChange,
}: {
  options: { value: V; label: string }[];
  value: V;
  onChange: (v: V) => void;
}) {
  return (
    <View style={styles.segmented}>
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <TouchableOpacity
            key={opt.value}
            style={[styles.segmentBtn, active && styles.segmentBtnActive]}
            onPress={() => onChange(opt.value)}
          >
            <Text
              style={[styles.segmentTxt, active && styles.segmentTxtActive]}
            >
              {opt.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

function BreakdownRow({
  label,
  value,
  tint,
}: {
  label: string;
  value: string;
  tint?: string;
}) {
  return (
    <View style={styles.breakRow}>
      <Text style={styles.breakLabel}>{label}</Text>
      <Text style={[styles.breakValue, tint ? { color: tint } : null]}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F" },
  content: { padding: 20, paddingBottom: 48 },
  center: {
    flex: 1,
    backgroundColor: "#0F0F0F",
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
    gap: 16,
  },
  errorTxt: {
    color: "#CCC",
    fontSize: 15,
    textAlign: "center",
    lineHeight: 22,
  },

  mealTitle: { color: "#FFFFFF", fontSize: 24, fontWeight: "700" },
  mealSubtitle: { color: "#999", fontSize: 14, marginTop: 4, marginBottom: 8 },

  section: {
    color: "#4ADE80",
    fontSize: 13,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginTop: 22,
    marginBottom: 10,
  },
  help: { color: "#777", fontSize: 12, marginBottom: 10, lineHeight: 16 },

  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#1A1A1A",
    borderRadius: 12,
    paddingHorizontal: 16,
  },
  input: {
    flex: 1,
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "600",
    paddingVertical: 14,
  },
  inputLarge: { fontSize: 24 },
  unit: { color: "#777", fontSize: 14, marginLeft: 8 },

  segmented: {
    flexDirection: "row",
    backgroundColor: "#1A1A1A",
    borderRadius: 12,
    padding: 4,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 10,
    alignItems: "center",
    borderRadius: 9,
  },
  segmentBtnActive: { backgroundColor: "#4ADE80" },
  segmentTxt: { color: "#999", fontSize: 14, fontWeight: "600" },
  segmentTxtActive: { color: "#0F0F0F" },

  warningBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    backgroundColor: "#3D2F0A",
    borderRadius: 12,
    padding: 12,
    marginTop: 12,
  },
  warningTxt: { color: "#FBBF24", fontSize: 13, lineHeight: 18, flex: 1 },

  breakdownCard: {
    backgroundColor: "#141414",
    borderRadius: 16,
    padding: 16,
    marginTop: 20,
  },
  breakRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 6,
  },
  breakLabel: { color: "#999", fontSize: 13, flex: 1, marginRight: 12 },
  breakValue: { color: "#FFFFFF", fontSize: 14, fontWeight: "600" },
  suggestedRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 14,
    marginTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#222",
  },
  suggestedLabel: { color: "#FFFFFF", fontSize: 15, fontWeight: "600" },
  suggestedValue: { color: "#4ADE80", fontSize: 22, fontWeight: "800" },

  primaryBtn: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 28,
  },
  primaryBtnTxt: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
  btnDisabled: { opacity: 0.6 },
  secondaryBtn: { paddingVertical: 14, alignItems: "center", marginTop: 4 },
  secondaryTxt: { color: "#999", fontSize: 14, fontWeight: "600" },
});
