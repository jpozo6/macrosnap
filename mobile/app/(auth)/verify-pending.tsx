/** Pantalla mostrada tras registrarse: pide verificar email. */

import { router, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import {
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { resendVerification } from "../../services/auth";

export default function VerifyPendingScreen() {
  const { email } = useLocalSearchParams<{ email?: string }>();
  const [sending, setSending] = useState(false);

  const handleResend = async () => {
    if (!email) {
      Alert.alert("Email desconocido", "Vuelve a registrarte o inicia sesión.");
      return;
    }
    setSending(true);
    try {
      await resendVerification(email);
      Alert.alert("Enviado", "Si el email existe, te hemos enviado un nuevo enlace.");
    } catch {
      Alert.alert("Error", "No se pudo reenviar el email.");
    } finally {
      setSending(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.iconWrap}>
        <Ionicons name="mail-outline" size={64} color="#4ADE80" />
      </View>
      <Text style={styles.title}>Confirma tu email</Text>
      <Text style={styles.body}>
        Te hemos enviado un enlace de verificación
        {email ? ` a ` : "."}
        {email ? <Text style={styles.email}>{email}</Text> : null}
        {email ? "." : ""}
      </Text>
      <Text style={styles.bodyMuted}>
        Abre el enlace desde ese correo y vuelve a iniciar sesión.
      </Text>

      <TouchableOpacity
        style={[styles.button, sending && styles.buttonDisabled]}
        onPress={handleResend}
        disabled={sending}
      >
        <Text style={styles.buttonText}>
          {sending ? "Reenviando..." : "Reenviar email"}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.secondary}
        onPress={() => router.replace("/(auth)/login")}
      >
        <Text style={styles.secondaryText}>Ir a iniciar sesión</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F", padding: 24, justifyContent: "center" },
  iconWrap: { alignItems: "center", marginBottom: 24 },
  title: { color: "#FFFFFF", fontSize: 24, fontWeight: "700", textAlign: "center", marginBottom: 12 },
  body: { color: "#CCC", fontSize: 15, textAlign: "center", lineHeight: 22 },
  email: { color: "#4ADE80", fontWeight: "600" },
  bodyMuted: { color: "#999", fontSize: 14, textAlign: "center", marginTop: 12, lineHeight: 20 },
  button: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 16,
    alignItems: "center",
    marginTop: 36,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
  secondary: { paddingVertical: 14, alignItems: "center", marginTop: 8 },
  secondaryText: { color: "#4ADE80", fontSize: 14, fontWeight: "600" },
});
