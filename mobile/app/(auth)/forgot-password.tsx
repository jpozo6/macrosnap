/** Pantalla para solicitar el email de restablecimiento de contraseña. */

import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
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
import { forgotPassword } from "../../services/auth";

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async () => {
    const trimmed = email.trim();
    if (!trimmed) {
      Alert.alert("Email vacío", "Introduce el email de tu cuenta.");
      return;
    }
    setSending(true);
    try {
      await forgotPassword(trimmed);
      setSent(true);
    } catch (err: any) {
      Alert.alert(
        "Error",
        err?.response?.data?.detail ?? "No se pudo enviar el email.",
      );
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <View style={styles.container}>
        <View style={styles.iconWrap}>
          <Ionicons name="mail-outline" size={64} color="#4ADE80" />
        </View>
        <Text style={styles.title}>Revisa tu correo</Text>
        <Text style={styles.body}>
          Si el email existe, te hemos enviado un enlace para restablecer tu
          contraseña.
        </Text>
        <Text style={styles.bodyMuted}>
          Abre el enlace desde ese correo para elegir una nueva contraseña.
        </Text>

        <TouchableOpacity
          style={styles.button}
          onPress={() => router.replace("/(auth)/login")}
        >
          <Text style={styles.buttonText}>Volver al login</Text>
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
        <Text style={styles.title}>Recuperar contraseña</Text>
        <Text style={styles.subtitle}>
          Introduce el email de tu cuenta y te enviaremos un enlace para
          restablecer la contraseña.
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

        <TouchableOpacity
          style={[styles.button, sending && styles.buttonDisabled]}
          onPress={handleSubmit}
          disabled={sending}
        >
          <Text style={styles.buttonText}>
            {sending ? "Enviando..." : "Enviar enlace"}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.secondary}
          onPress={() => router.replace("/(auth)/login")}
        >
          <Text style={styles.secondaryText}>Volver al login</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F", padding: 24, justifyContent: "center" },
  content: { flex: 1, justifyContent: "center" },
  iconWrap: { alignItems: "center", marginBottom: 24 },
  title: { color: "#FFFFFF", fontSize: 24, fontWeight: "700", textAlign: "center", marginBottom: 12 },
  subtitle: { color: "#999", fontSize: 15, marginBottom: 24, textAlign: "center", lineHeight: 22 },
  body: { color: "#CCC", fontSize: 15, textAlign: "center", lineHeight: 22 },
  bodyMuted: { color: "#999", fontSize: 14, textAlign: "center", marginTop: 12, lineHeight: 20 },
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
  secondary: { paddingVertical: 14, alignItems: "center", marginTop: 8 },
  secondaryText: { color: "#4ADE80", fontSize: 14, fontWeight: "600" },
});
