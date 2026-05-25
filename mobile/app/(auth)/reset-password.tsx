/** Pantalla destino del enlace de reset de contraseña. */

import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import {
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { resetPassword } from "../../services/auth";
import { showAlert } from "../../services/alert";

export default function ResetPasswordScreen() {
  const { token } = useLocalSearchParams<{ token?: string }>();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);

  if (!token) {
    return (
      <View style={styles.container}>
        <View style={styles.iconWrap}>
          <Ionicons name="alert-circle" size={72} color="#F87171" />
        </View>
        <Text style={styles.title}>Enlace no válido</Text>
        <Text style={styles.body}>
          Falta el token en la URL. Solicita un nuevo enlace desde el login.
        </Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => router.replace("/(auth)/forgot-password")}
        >
          <Text style={styles.buttonText}>Pedir nuevo enlace</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const handleSubmit = async () => {
    if (password.length < 8) {
      showAlert("Contraseña corta", "La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (password !== confirm) {
      showAlert("No coinciden", "Las contraseñas introducidas no coinciden.");
      return;
    }
    setSubmitting(true);
    try {
      await resetPassword(token, password, confirm);
      setDone(true);
    } catch (err: any) {
      showAlert(
        "Error",
        err?.response?.data?.detail ?? "No se pudo restablecer la contraseña.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <View style={styles.container}>
        <View style={styles.iconWrap}>
          <Ionicons name="checkmark-circle" size={72} color="#4ADE80" />
        </View>
        <Text style={styles.title}>Contraseña actualizada</Text>
        <Text style={styles.body}>
          Ya puedes iniciar sesión con tu nueva contraseña.
        </Text>
        <TouchableOpacity
          style={styles.button}
          onPress={() => router.replace("/(auth)/login")}
        >
          <Text style={styles.buttonText}>Iniciar sesión</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Nueva contraseña</Text>
        <Text style={styles.subtitle}>
          Elige la contraseña con la que iniciarás sesión a partir de ahora.
        </Text>

        <Text style={styles.label}>Nueva contraseña</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          placeholder="Al menos 8 caracteres"
          placeholderTextColor="#555"
          secureTextEntry
          autoComplete="password-new"
          textContentType="newPassword"
        />

        <Text style={styles.label}>Confirmar contraseña</Text>
        <TextInput
          style={styles.input}
          value={confirm}
          onChangeText={setConfirm}
          placeholder="Repite la contraseña"
          placeholderTextColor="#555"
          secureTextEntry
          autoComplete="password-new"
          textContentType="newPassword"
        />

        <TouchableOpacity
          style={[styles.button, submitting && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={submitting}
        >
          <Text style={styles.buttonText}>
            {submitting ? "Guardando..." : "Cambiar contraseña"}
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F", padding: 24, justifyContent: "center" },
  content: { flex: 1, justifyContent: "center" },
  iconWrap: { alignItems: "center", marginBottom: 16 },
  title: { color: "#FFFFFF", fontSize: 24, fontWeight: "700", textAlign: "center", marginBottom: 12 },
  subtitle: { color: "#999", fontSize: 15, marginBottom: 16, textAlign: "center", lineHeight: 22 },
  body: { color: "#CCC", fontSize: 15, textAlign: "center", lineHeight: 22, marginTop: 12 },
  label: { color: "#CCC", fontSize: 14, fontWeight: "500", marginTop: 16, marginBottom: 8 },
  input: {
    backgroundColor: "#1A1A1A",
    color: "#FFFFFF",
    fontSize: 16,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  button: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 28,
    paddingHorizontal: 32,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
});
