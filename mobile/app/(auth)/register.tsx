/** Pantalla de registro de nueva cuenta. */

import { Link, router } from "expo-router";
import { useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useAuthStore } from "../../store/useAuthStore";

export default function RegisterScreen() {
  const [email, setEmail] = useState("");
  const [emailConfirm, setEmailConfirm] = useState("");
  const [password, setPassword] = useState("");
  const { register, isLoading } = useAuthStore();

  const handleSubmit = async () => {
    const e1 = email.trim().toLowerCase();
    const e2 = emailConfirm.trim().toLowerCase();

    if (!e1 || !e2 || !password) {
      Alert.alert("Datos incompletos", "Rellena todos los campos.");
      return;
    }
    if (e1 !== e2) {
      Alert.alert("Emails distintos", "Los correos electrónicos no coinciden.");
      return;
    }
    if (password.length < 8) {
      Alert.alert("Contraseña corta", "Usa al menos 8 caracteres.");
      return;
    }

    try {
      await register(e1, e2, password);
      router.replace({ pathname: "/(auth)/verify-pending", params: { email: e1 } });
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 409) {
        Alert.alert("Email en uso", "Ya existe una cuenta con ese email.");
      } else if (status === 422) {
        const detail = err?.response?.data?.detail;
        const msg = Array.isArray(detail)
          ? detail.map((d: any) => d.msg).join("\n")
          : detail ?? "Datos inválidos.";
        Alert.alert("Datos inválidos", msg);
      } else {
        Alert.alert("Error", err?.response?.data?.detail ?? "No se pudo registrar.");
      }
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <Text style={styles.title}>Crea tu cuenta</Text>
        <Text style={styles.subtitle}>
          Te enviaremos un email para confirmar tu dirección.
        </Text>

        <Text style={styles.label}>Email</Text>
        <TextInput
          style={styles.input}
          value={email}
          onChangeText={setEmail}
          placeholder="tu@email.com"
          placeholderTextColor="#555"
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          textContentType="emailAddress"
        />

        <Text style={styles.label}>Confirmar email</Text>
        <TextInput
          style={styles.input}
          value={emailConfirm}
          onChangeText={setEmailConfirm}
          placeholder="tu@email.com"
          placeholderTextColor="#555"
          autoCapitalize="none"
          keyboardType="email-address"
          autoComplete="email"
          textContentType="emailAddress"
        />

        <Text style={styles.label}>Contraseña</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          placeholder="Mínimo 8 caracteres"
          placeholderTextColor="#555"
          secureTextEntry
          autoComplete="new-password"
          textContentType="newPassword"
        />

        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={isLoading}
        >
          <Text style={styles.buttonText}>
            {isLoading ? "Creando cuenta..." : "Crear cuenta"}
          </Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>¿Ya tienes cuenta?</Text>
          <Link href="/(auth)/login" style={styles.footerLink}>
            Iniciar sesión
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F" },
  content: { padding: 24, paddingBottom: 48 },
  title: { color: "#FFFFFF", fontSize: 28, fontWeight: "700", marginBottom: 8, marginTop: 12 },
  subtitle: { color: "#999", fontSize: 15, marginBottom: 24 },
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
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
  footer: { flexDirection: "row", justifyContent: "center", marginTop: 24, gap: 6 },
  footerText: { color: "#999", fontSize: 14 },
  footerLink: { color: "#4ADE80", fontSize: 14, fontWeight: "600" },
});
