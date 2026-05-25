/** Pestaña "Diabetes": historial de bolos + configuración del perfil clínico.
 *
 * Flujo:
 *   - Sin perfil → empty state → al pulsar "Configurar" se abre el formulario.
 *   - Con perfil → segmented "Historial / Perfil". Aterriza en historial; el
 *     perfil queda accesible para editar/desactivar.
 *
 * El formulario es la única vía para activar/desactivar el modo diabético
 * (guardar = activar; "Desactivar modo" = DELETE del perfil).
 */

import { Ionicons } from "@expo/vector-icons";
import { router, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { showAlert, showConfirm } from "../../services/alert";
import { getMeals } from "../../services/api";
import { TIME_SLOT_LABELS } from "../../services/timeSlot";
import { useDiabeticStore } from "../../store/useDiabeticStore";
import type {
  BolusRoundingStep,
  DiabeticProfileUpsert,
  ExerciseLevel,
  Meal,
} from "../../types";

const EXERCISE_LABEL: Record<ExerciseLevel, string> = {
  none: "Sin ejercicio",
  moderate: "Ejercicio moderado",
  intense: "Ejercicio intenso",
};

const ROUNDING_STEPS: BolusRoundingStep[] = [0.1, 0.5, 1.0];

interface DraftState {
  ration_grams: string;
  target_glucose: string;
  hypo_threshold: string;
  bolus_rounding_step: BolusRoundingStep;
  // Mostramos los factores de ejercicio como porcentaje positivo (20 = -20%).
  exercise_moderate_pct: string;
  exercise_intense_pct: string;
  ipr_breakfast: string;
  ipr_lunch: string;
  ipr_dinner: string;
  isf_breakfast: string;
  isf_lunch: string;
  isf_dinner: string;
}

const DEFAULT_DRAFT: DraftState = {
  ration_grams: "10",
  target_glucose: "110",
  hypo_threshold: "70",
  bolus_rounding_step: 0.5,
  exercise_moderate_pct: "20",
  exercise_intense_pct: "40",
  ipr_breakfast: "",
  ipr_lunch: "",
  ipr_dinner: "",
  isf_breakfast: "",
  isf_lunch: "",
  isf_dinner: "",
};

function num(s: string): number {
  // `Number("")` da 0 — peligroso aquí. Lo distinguimos por `isEmpty`.
  return Number(s.replace(",", "."));
}

function isEmpty(s: string): boolean {
  return s.trim() === "";
}

export default function DiabetesScreen() {
  const { profile, isLoaded, isSaving, load, save, deactivate } =
    useDiabeticStore();
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState<DraftState>(DEFAULT_DRAFT);
  // Cuando hay perfil, segmentamos entre historial (default) y perfil.
  const [view, setView] = useState<"history" | "profile">("history");

  useEffect(() => {
    void load();
  }, [load]);

  // Cuando llega el perfil del servidor, hidratamos el draft y mostramos formulario.
  useEffect(() => {
    if (profile) {
      setDraft({
        ration_grams: String(profile.ration_grams),
        target_glucose: String(profile.target_glucose),
        hypo_threshold: String(profile.hypo_threshold),
        bolus_rounding_step: profile.bolus_rounding_step,
        exercise_moderate_pct: String(
          Math.round(Math.abs(profile.exercise_moderate_factor) * 100),
        ),
        exercise_intense_pct: String(
          Math.round(Math.abs(profile.exercise_intense_factor) * 100),
        ),
        ipr_breakfast: String(profile.ipr_breakfast),
        ipr_lunch: String(profile.ipr_lunch),
        ipr_dinner: String(profile.ipr_dinner),
        isf_breakfast: String(profile.isf_breakfast),
        isf_lunch: String(profile.isf_lunch),
        isf_dinner: String(profile.isf_dinner),
      });
      setShowForm(true);
    }
  }, [profile]);

  const validationError = useMemo(() => {
    const required: (keyof DraftState)[] = [
      "ipr_breakfast",
      "ipr_lunch",
      "ipr_dinner",
      "isf_breakfast",
      "isf_lunch",
      "isf_dinner",
    ];
    for (const k of required) {
      if (isEmpty(draft[k] as string)) {
        return "Rellena los ratios de las tres franjas (IPR e ISF).";
      }
    }
    const ipr = [draft.ipr_breakfast, draft.ipr_lunch, draft.ipr_dinner].map(num);
    if (ipr.some((v) => !(v >= 0.1 && v <= 10))) {
      return "Los IPR deben estar entre 0.1 y 10 U/ración.";
    }
    const isf = [draft.isf_breakfast, draft.isf_lunch, draft.isf_dinner].map(num);
    if (isf.some((v) => !(Number.isInteger(v) && v >= 5 && v <= 400))) {
      return "Los ISF deben ser enteros entre 5 y 400 mg/dL por U.";
    }
    if (!(num(draft.ration_grams) >= 1 && num(draft.ration_grams) <= 20)) {
      return "Los gramos por ración deben estar entre 1 y 20.";
    }
    const target = num(draft.target_glucose);
    if (!(target >= 70 && target <= 180)) {
      return "El objetivo de glucemia debe estar entre 70 y 180 mg/dL.";
    }
    const hypo = num(draft.hypo_threshold);
    if (!(hypo >= 50 && hypo <= 100)) {
      return "El umbral de hipoglucemia debe estar entre 50 y 100 mg/dL.";
    }
    const modPct = num(draft.exercise_moderate_pct);
    const intPct = num(draft.exercise_intense_pct);
    if (!(modPct >= 0 && modPct <= 90 && intPct >= 0 && intPct <= 90)) {
      return "Los porcentajes de ejercicio deben estar entre 0 y 90.";
    }
    return null;
  }, [draft]);

  const handleSave = async () => {
    if (validationError) {
      showAlert("Datos inválidos", validationError);
      return;
    }
    const payload: DiabeticProfileUpsert = {
      ration_grams: num(draft.ration_grams),
      target_glucose: num(draft.target_glucose),
      hypo_threshold: num(draft.hypo_threshold),
      bolus_rounding_step: draft.bolus_rounding_step,
      // Convertimos % positivo introducido por el usuario a fracción negativa
      // tal y como espera el backend (-0.20 = -20%).
      exercise_moderate_factor: -num(draft.exercise_moderate_pct) / 100,
      exercise_intense_factor: -num(draft.exercise_intense_pct) / 100,
      ipr_breakfast: num(draft.ipr_breakfast),
      ipr_lunch: num(draft.ipr_lunch),
      ipr_dinner: num(draft.ipr_dinner),
      isf_breakfast: num(draft.isf_breakfast),
      isf_lunch: num(draft.isf_lunch),
      isf_dinner: num(draft.isf_dinner),
    };
    try {
      await save(payload);
      showAlert("Guardado", "Tu perfil diabético se ha actualizado.");
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ??
        err?.message ??
        "No se pudo guardar el perfil.";
      showAlert("Error", String(detail));
    }
  };

  const handleDeactivate = () => {
    showConfirm(
      "Desactivar modo diabético",
      "Se borrará tu perfil clínico y los cálculos de bolo dejarán de estar disponibles. Las comidas que ya tengan bolo registrado se conservan.",
      {
        confirmLabel: "Desactivar",
        destructive: true,
        onConfirm: async () => {
          try {
            await deactivate();
            setShowForm(false);
            setDraft(DEFAULT_DRAFT);
          } catch (err: any) {
            showAlert("Error", err?.message ?? "No se pudo desactivar.");
          }
        },
      },
    );
  };

  if (!isLoaded) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator color="#4ADE80" />
      </View>
    );
  }

  if (!profile && !showForm) {
    return (
      <EmptyState
        onActivate={() => {
          setShowForm(true);
          setView("profile");
        }}
      />
    );
  }

  // Con perfil, ofrecemos historial + perfil. Sin perfil (recién creado o
  // editando por primera vez tras CTA), solo perfil.
  if (profile && view === "history") {
    return (
      <View style={styles.container}>
        <SegmentedTabs view={view} onChange={setView} />
        <BolusHistoryView rationGrams={profile.ration_grams} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      {profile ? <SegmentedTabs view={view} onChange={setView} /> : null}
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>Perfil diabético</Text>
        <Text style={styles.subtitle}>
          Estos valores los receta tu endocrino. Revísalos con él antes de
          usarlos en la calculadora del bolo.
        </Text>

        <SectionTitle>Ración y objetivos</SectionTitle>

        <NumberField
          label="Gramos por ración"
          unit="g"
          value={draft.ration_grams}
          onChangeText={(v) => setDraft({ ...draft, ration_grams: v })}
          help="En España suelen ser 10 g de HC por ración."
        />
        <NumberField
          label="Objetivo de glucemia"
          unit="mg/dL"
          value={draft.target_glucose}
          onChangeText={(v) => setDraft({ ...draft, target_glucose: v })}
        />
        <NumberField
          label="Umbral de hipoglucemia"
          unit="mg/dL"
          value={draft.hypo_threshold}
          onChangeText={(v) => setDraft({ ...draft, hypo_threshold: v })}
          help="Por debajo de este valor, la app te avisará para tomar HC rápidos."
        />

        <Text style={styles.fieldLabel}>Paso de redondeo del bolo</Text>
        <View style={styles.segmented}>
          {ROUNDING_STEPS.map((step) => {
            const active = draft.bolus_rounding_step === step;
            return (
              <TouchableOpacity
                key={step}
                style={[styles.segmentBtn, active && styles.segmentBtnActive]}
                onPress={() => setDraft({ ...draft, bolus_rounding_step: step })}
              >
                <Text
                  style={[
                    styles.segmentTxt,
                    active && styles.segmentTxtActive,
                  ]}
                >
                  {step.toFixed(step === 1 ? 0 : 1)} U
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <SectionTitle>Ratios por franja horaria</SectionTitle>

        <SlotBlock
          title="Desayuno"
          range="00:00 – 11:00"
          ipr={draft.ipr_breakfast}
          isf={draft.isf_breakfast}
          onIprChange={(v) => setDraft({ ...draft, ipr_breakfast: v })}
          onIsfChange={(v) => setDraft({ ...draft, isf_breakfast: v })}
        />
        <SlotBlock
          title="Comida"
          range="11:00 – 17:00"
          ipr={draft.ipr_lunch}
          isf={draft.isf_lunch}
          onIprChange={(v) => setDraft({ ...draft, ipr_lunch: v })}
          onIsfChange={(v) => setDraft({ ...draft, isf_lunch: v })}
        />
        <SlotBlock
          title="Cena"
          range="17:00 – 24:00"
          ipr={draft.ipr_dinner}
          isf={draft.isf_dinner}
          onIprChange={(v) => setDraft({ ...draft, ipr_dinner: v })}
          onIsfChange={(v) => setDraft({ ...draft, isf_dinner: v })}
        />

        <SectionTitle>Ajuste por ejercicio</SectionTitle>
        <Text style={styles.help}>
          Reducción del bolo cuando hayas hecho ejercicio reciente o lo vayas a
          hacer en las próximas horas.
        </Text>
        <NumberField
          label="Ejercicio moderado"
          unit="%"
          value={draft.exercise_moderate_pct}
          onChangeText={(v) =>
            setDraft({ ...draft, exercise_moderate_pct: v })
          }
        />
        <NumberField
          label="Ejercicio intenso"
          unit="%"
          value={draft.exercise_intense_pct}
          onChangeText={(v) => setDraft({ ...draft, exercise_intense_pct: v })}
        />

        <TouchableOpacity
          style={[styles.primaryBtn, isSaving && styles.btnDisabled]}
          onPress={handleSave}
          disabled={isSaving}
        >
          <Text style={styles.primaryBtnTxt}>
            {isSaving ? "Guardando..." : profile ? "Guardar cambios" : "Activar modo diabético"}
          </Text>
        </TouchableOpacity>

        {profile ? (
          <TouchableOpacity
            style={styles.destructiveBtn}
            onPress={handleDeactivate}
          >
            <Text style={styles.destructiveTxt}>Desactivar modo diabético</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={styles.secondaryBtn}
            onPress={() => setShowForm(false)}
          >
            <Text style={styles.secondaryTxt}>Cancelar</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

// ===== Subcomponentes =====

function SegmentedTabs({
  view,
  onChange,
}: {
  view: "history" | "profile";
  onChange: (v: "history" | "profile") => void;
}) {
  return (
    <View style={styles.tabBar}>
      {(["history", "profile"] as const).map((v) => {
        const active = view === v;
        return (
          <TouchableOpacity
            key={v}
            style={[styles.tabBtn, active && styles.tabBtnActive]}
            onPress={() => onChange(v)}
          >
            <Text style={[styles.tabTxt, active && styles.tabTxtActive]}>
              {v === "history" ? "Historial" : "Perfil"}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

function BolusHistoryView({ rationGrams }: { rationGrams: number }) {
  const [meals, setMeals] = useState<Meal[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      // Pedimos las últimas 50 comidas; filtramos client-side las que tienen bolo.
      const all = await getMeals({ limit: 50, offset: 0 });
      setMeals(all.filter((m) => m.bolus));
    } catch (err: any) {
      setError(err?.message ?? "No se pudo cargar el historial.");
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      void refresh();
    }, [refresh]),
  );

  if (!meals && !error) {
    return (
      <View style={styles.loaderContainer}>
        <ActivityIndicator color="#4ADE80" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.historyEmpty}>
        <Text style={styles.historyEmptyTitle}>Error</Text>
        <Text style={styles.historyEmptyBody}>{error}</Text>
      </View>
    );
  }

  if (meals && meals.length === 0) {
    return (
      <View style={styles.historyEmpty}>
        <Ionicons name="medkit-outline" size={48} color="#4ADE80" />
        <Text style={styles.historyEmptyTitle}>Sin bolos registrados</Text>
        <Text style={styles.historyEmptyBody}>
          Analiza una comida y pulsa "Calcular bolo" para empezar a llevar el
          control de la insulina por comida.
        </Text>
      </View>
    );
  }

  return (
    <FlatList
      data={meals!}
      keyExtractor={(m) => String(m.id)}
      contentContainerStyle={styles.historyList}
      renderItem={({ item }) => (
        <BolusHistoryRow meal={item} rationGrams={rationGrams} />
      )}
    />
  );
}

function BolusHistoryRow({
  meal,
  rationGrams: _rationGrams,
}: {
  meal: Meal;
  rationGrams: number;
}) {
  const b = meal.bolus!;
  const when = new Date(meal.created_at).toLocaleString("es", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
  const differsFromSuggested =
    Math.abs(b.bolus_total_units - b.bolus_suggested_units) > 0.05;
  return (
    <TouchableOpacity
      style={styles.historyCard}
      onPress={() => router.push(`/result/${meal.id}`)}
      activeOpacity={0.7}
    >
      <View style={styles.historyHeader}>
        <Text style={styles.historyMealName} numberOfLines={1}>
          {meal.meal_name}
        </Text>
        <Text style={styles.historyTime}>{when}</Text>
      </View>
      <View style={styles.historyBolusRow}>
        <Text style={styles.historyBolusValue}>
          {b.bolus_total_units.toFixed(1)} U
        </Text>
        {differsFromSuggested && (
          <Text style={styles.historyBolusSuggested}>
            sugerido {b.bolus_suggested_units.toFixed(1)} U
          </Text>
        )}
      </View>
      <Text style={styles.historyDetails}>
        {b.rations_hc} raciones · {b.glucose_mg_dl} mg/dL ·{" "}
        {TIME_SLOT_LABELS[b.slot]}
        {b.exercise_level !== "none"
          ? ` · ${EXERCISE_LABEL[b.exercise_level].toLowerCase()}`
          : ""}
      </Text>
    </TouchableOpacity>
  );
}

function EmptyState({ onActivate }: { onActivate: () => void }) {
  return (
    <View style={styles.emptyContainer}>
      <View style={styles.emptyIcon}>
        <Ionicons name="medkit-outline" size={56} color="#4ADE80" />
      </View>
      <Text style={styles.emptyTitle}>Modo diabético</Text>
      <Text style={styles.emptyBody}>
        Configura tu perfil clínico (ratios por franja, sensibilidad,
        objetivos) y MacroSnap te propondrá el bolo de insulina al analizar
        cada comida.
      </Text>
      <Text style={styles.emptyDisclaimer}>
        La app sugiere, tú decides. No sustituye el consejo de tu endocrino.
      </Text>
      <TouchableOpacity style={styles.primaryBtn} onPress={onActivate}>
        <Text style={styles.primaryBtnTxt}>Configurar mi perfil</Text>
      </TouchableOpacity>
    </View>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return <Text style={styles.sectionTitle}>{children}</Text>;
}

function NumberField({
  label,
  unit,
  value,
  onChangeText,
  help,
}: {
  label: string;
  unit?: string;
  value: string;
  onChangeText: (v: string) => void;
  help?: string;
}) {
  return (
    <View style={styles.fieldContainer}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChangeText}
          keyboardType="decimal-pad"
          placeholderTextColor="#555"
        />
        {unit ? <Text style={styles.unit}>{unit}</Text> : null}
      </View>
      {help ? <Text style={styles.help}>{help}</Text> : null}
    </View>
  );
}

function SlotBlock({
  title,
  range,
  ipr,
  isf,
  onIprChange,
  onIsfChange,
}: {
  title: string;
  range: string;
  ipr: string;
  isf: string;
  onIprChange: (v: string) => void;
  onIsfChange: (v: string) => void;
}) {
  return (
    <View style={styles.slotBlock}>
      <View style={styles.slotHeader}>
        <Text style={styles.slotTitle}>{title}</Text>
        <Text style={styles.slotRange}>{range}</Text>
      </View>
      <View style={styles.slotRow}>
        <View style={styles.slotCol}>
          <Text style={styles.slotFieldLabel}>Insulina / ración</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={ipr}
              onChangeText={onIprChange}
              keyboardType="decimal-pad"
              placeholder="1.0"
              placeholderTextColor="#555"
            />
            <Text style={styles.unit}>U</Text>
          </View>
        </View>
        <View style={styles.slotCol}>
          <Text style={styles.slotFieldLabel}>Sensibilidad</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={isf}
              onChangeText={onIsfChange}
              keyboardType="number-pad"
              placeholder="50"
              placeholderTextColor="#555"
            />
            <Text style={styles.unit}>mg/dL/U</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F" },
  content: { padding: 20, paddingBottom: 48 },

  loaderContainer: {
    flex: 1,
    backgroundColor: "#0F0F0F",
    justifyContent: "center",
    alignItems: "center",
  },

  // Empty state
  emptyContainer: {
    flex: 1,
    backgroundColor: "#0F0F0F",
    padding: 32,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyIcon: { marginBottom: 24 },
  emptyTitle: {
    color: "#FFFFFF",
    fontSize: 24,
    fontWeight: "700",
    marginBottom: 12,
    textAlign: "center",
  },
  emptyBody: {
    color: "#CCC",
    fontSize: 15,
    lineHeight: 22,
    textAlign: "center",
    marginBottom: 24,
  },
  emptyDisclaimer: {
    color: "#FBBF24",
    fontSize: 13,
    textAlign: "center",
    marginBottom: 32,
    fontStyle: "italic",
  },

  // Form
  title: { color: "#FFFFFF", fontSize: 28, fontWeight: "700", marginBottom: 4 },
  subtitle: { color: "#999", fontSize: 14, marginBottom: 20, lineHeight: 20 },
  sectionTitle: {
    color: "#4ADE80",
    fontSize: 13,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginTop: 24,
    marginBottom: 12,
  },

  fieldContainer: { marginBottom: 16 },
  fieldLabel: { color: "#FFFFFF", fontSize: 14, fontWeight: "500", marginBottom: 8 },
  help: { color: "#777", fontSize: 12, marginTop: 6, lineHeight: 16 },

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
    fontSize: 16,
    fontWeight: "600",
    paddingVertical: 12,
  },
  unit: { color: "#777", fontSize: 14, marginLeft: 8 },

  // Segmented
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

  // Slot
  slotBlock: {
    backgroundColor: "#141414",
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  slotHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
    marginBottom: 12,
  },
  slotTitle: { color: "#FFFFFF", fontSize: 16, fontWeight: "700" },
  slotRange: { color: "#777", fontSize: 12 },
  slotRow: { flexDirection: "row", gap: 12 },
  slotCol: { flex: 1 },
  slotFieldLabel: { color: "#999", fontSize: 12, marginBottom: 6 },

  // Buttons
  primaryBtn: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 28,
  },
  primaryBtnTxt: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
  btnDisabled: { opacity: 0.6 },

  secondaryBtn: { paddingVertical: 14, alignItems: "center", marginTop: 8 },
  secondaryTxt: { color: "#4ADE80", fontSize: 14, fontWeight: "600" },

  destructiveBtn: {
    backgroundColor: "#2A1515",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 12,
  },
  destructiveTxt: { color: "#F87171", fontSize: 15, fontWeight: "600" },

  // Tabs superiores (Historial / Perfil)
  tabBar: {
    flexDirection: "row",
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 4,
    gap: 8,
  },
  tabBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: "#1A1A1A",
    alignItems: "center",
  },
  tabBtnActive: { backgroundColor: "#4ADE80" },
  tabTxt: { color: "#999", fontSize: 14, fontWeight: "600" },
  tabTxtActive: { color: "#0F0F0F" },

  // Historial
  historyList: { padding: 16, gap: 10 },
  historyEmpty: {
    flex: 1,
    backgroundColor: "#0F0F0F",
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
    gap: 12,
  },
  historyEmptyTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "700",
    marginTop: 4,
  },
  historyEmptyBody: {
    color: "#CCC",
    fontSize: 14,
    lineHeight: 20,
    textAlign: "center",
  },
  historyCard: {
    backgroundColor: "#1A1A1A",
    borderRadius: 14,
    padding: 14,
    marginBottom: 8,
  },
  historyHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "baseline",
    marginBottom: 6,
    gap: 8,
  },
  historyMealName: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
    flexShrink: 1,
  },
  historyTime: { color: "#666", fontSize: 12 },
  historyBolusRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
    marginBottom: 4,
  },
  historyBolusValue: { color: "#4ADE80", fontSize: 22, fontWeight: "800" },
  historyBolusSuggested: { color: "#777", fontSize: 12 },
  historyDetails: { color: "#999", fontSize: 12 },
});
