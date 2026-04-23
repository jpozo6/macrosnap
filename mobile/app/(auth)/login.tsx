/** Pantalla de inicio de sesión. */

import { Link, router } from "expo-router";
import { useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useAuthStore } from "../../store/useAuthStore";

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { login, isLoading } = useAuthStore();

  const handleSubmit = async () => {
    if (!email.trim() || !password) {
      Alert.alert("Datos incompletos", "Introduce email y contraseña.");
      return;
    }
    try {
      await login(email.trim(), password);
      router.replace("/(tabs)/camera");
    } catch (err: any) {
      const status = err?.response?.status;
      if (status === 403) {
        Alert.alert(
          "Email no verificado",
          "Revisa tu bandeja de entrada y pulsa el enlace de confirmación.",
        );
        router.push({ pathname: "/(auth)/verify-pending", params: { email: email.trim() } });
      } else if (status === 401) {
        Alert.alert("Credenciales incorrectas", "Revisa tu email y contraseña.");
      } else {
        Alert.alert("Error", err?.response?.data?.detail ?? "No se pudo iniciar sesión.");
      }
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Bienvenido de vuelta</Text>
        <Text style={styles.subtitle}>Inicia sesión para continuar.</Text>

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

        <Text style={styles.label}>Contraseña</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          placeholder="Contraseña"
          placeholderTextColor="#555"
          secureTextEntry
          autoComplete="password"
          textContentType="password"
        />

        <TouchableOpacity
          style={[styles.button, isLoading && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={isLoading}
        >
          <Text style={styles.buttonText}>
            {isLoading ? "Entrando..." : "Iniciar sesión"}
          </Text>
        </TouchableOpacity>

        <View style={styles.footer}>
          <Text style={styles.footerText}>¿No tienes cuenta?</Text>
          <Link href="/(auth)/register" style={styles.footerLink}>
            Crear cuenta
          </Link>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F" },
  content: { flex: 1, padding: 24, justifyContent: "center" },
  title: { color: "#FFFFFF", fontSize: 28, fontWeight: "700", marginBottom: 8 },
  subtitle: { color: "#999", fontSize: 15, marginBottom: 32 },
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
