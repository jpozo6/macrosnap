/** Pantalla de perfil: configurar objetivos diarios de macros. */

import { useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
} from "react-native";
import { useMealStore } from "../../store/useMealStore";
import { useAuthStore } from "../../store/useAuthStore";
import { getMacroGoals, saveMacroGoals } from "../../services/storage";
import { showAlert, showConfirm } from "../../services/alert";
import type { MacroGoals } from "../../types";

interface GoalField {
  key: keyof MacroGoals;
  label: string;
  unit: string;
  color: string;
}

const GOAL_FIELDS: GoalField[] = [
  { key: "calories", label: "Calorías", unit: "kcal", color: "#4ADE80" },
  { key: "protein_g", label: "Proteína", unit: "g", color: "#4ADE80" },
  { key: "carbs_g", label: "Carbohidratos", unit: "g", color: "#60A5FA" },
  { key: "fat_g", label: "Grasa", unit: "g", color: "#FBBF24" },
];

export default function ProfileScreen() {
  const { goals, setGoals } = useMealStore();
  const { user, logout } = useAuthStore();
  const [draft, setDraft] = useState<MacroGoals>(goals);

  const handleLogout = () => {
    showConfirm("Cerrar sesión", "¿Seguro que quieres salir?", {
      confirmLabel: "Salir",
      destructive: true,
      onConfirm: () => { void logout(); },
    });
  };

  useEffect(() => {
    getMacroGoals().then((saved) => {
      setDraft(saved);
      setGoals(saved);
    });
  }, []);

  const handleSave = async () => {
    await saveMacroGoals(draft);
    setGoals(draft);
    showAlert("Guardado", "Tus objetivos se han actualizado.");
  };

  const updateField = (key: keyof MacroGoals, value: string) => {
    const num = parseInt(value, 10);
    setDraft((prev) => ({ ...prev, [key]: isNaN(num) ? 0 : num }));
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Objetivos diarios</Text>
      <Text style={styles.subtitle}>
        Configura tus metas de macronutrientes para el día
      </Text>

      {GOAL_FIELDS.map((field) => (
        <View key={field.key} style={styles.fieldContainer}>
          <View style={styles.fieldHeader}>
            <View style={[styles.dot, { backgroundColor: field.color }]} />
            <Text style={styles.fieldLabel}>{field.label}</Text>
          </View>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={String(draft[field.key])}
              onChangeText={(v) => updateField(field.key, v)}
              keyboardType="numeric"
              placeholderTextColor="#666666"
            />
            <Text style={styles.unit}>{field.unit}</Text>
          </View>
        </View>
      ))}

      <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
        <Text style={styles.saveButtonText}>Guardar objetivos</Text>
      </TouchableOpacity>

      {user ? (
        <View style={styles.accountCard}>
          <Text style={styles.accountLabel}>Cuenta</Text>
          <Text style={styles.accountEmail}>{user.email}</Text>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutText}>Cerrar sesión</Text>
          </TouchableOpacity>
        </View>
      ) : null}

      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>MacroSnap v1.0</Text>
        <Text style={styles.infoText}>
          Analiza tus comidas con IA para llevar un control de tus macronutrientes.
        </Text>
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
    paddingBottom: 40,
  },
  title: {
    color: "#FFFFFF",
    fontSize: 28,
    fontWeight: "700",
    marginBottom: 4,
  },
  subtitle: {
    color: "#666666",
    fontSize: 14,
    marginBottom: 28,
  },
  fieldContainer: {
    marginBottom: 20,
  },
  fieldHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  fieldLabel: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "500",
  },
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
  unit: {
    color: "#666666",
    fontSize: 15,
  },
  saveButton: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 12,
    marginBottom: 32,
  },
  saveButtonText: {
    color: "#0F0F0F",
    fontSize: 16,
    fontWeight: "700",
  },
  infoCard: {
    backgroundColor: "#1A1A1A",
    borderRadius: 16,
    padding: 20,
  },
  infoTitle: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 8,
  },
  infoText: {
    color: "#999999",
    fontSize: 14,
    lineHeight: 20,
  },
  accountCard: {
    backgroundColor: "#1A1A1A",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  accountLabel: {
    color: "#999",
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 6,
  },
  accountEmail: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
    marginBottom: 16,
  },
  logoutButton: {
    backgroundColor: "#2A1515",
    borderRadius: 12,
    paddingVertical: 12,
    alignItems: "center",
  },
  logoutText: {
    color: "#F87171",
    fontSize: 15,
    fontWeight: "600",
  },
});
