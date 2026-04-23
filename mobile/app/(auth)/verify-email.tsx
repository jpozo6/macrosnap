/** Pantalla destino del enlace del email de verificación. */

import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import api from "../../services/api";

type Status = "loading" | "ok" | "error";

export default function VerifyEmailScreen() {
  const { token } = useLocalSearchParams<{ token?: string }>();
  const [status, setStatus] = useState<Status>("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Falta el token en la URL.");
      return;
    }
    api
      .get("/auth/verify-email", { params: { token } })
      .then((res) => {
        setStatus("ok");
        setMessage(res.data?.message ?? "Email verificado correctamente.");
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err?.response?.data?.detail ?? "No se pudo verificar el email.");
      });
  }, [token]);

  if (status === "loading") {
    return (
      <View style={styles.container}>
        <ActivityIndicator color="#4ADE80" size="large" />
        <Text style={styles.body}>Verificando tu email...</Text>
      </View>
    );
  }

  const isOk = status === "ok";

  return (
    <View style={styles.container}>
      <View style={styles.iconWrap}>
        <Ionicons
          name={isOk ? "checkmark-circle" : "alert-circle"}
          size={72}
          color={isOk ? "#4ADE80" : "#F87171"}
        />
      </View>
      <Text style={styles.title}>
        {isOk ? "Cuenta verificada" : "No se pudo verificar"}
      </Text>
      <Text style={styles.body}>{message}</Text>

      <TouchableOpacity
        style={styles.button}
        onPress={() => router.replace("/(auth)/login")}
      >
        <Text style={styles.buttonText}>Iniciar sesión</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0F0F0F", padding: 24, justifyContent: "center", alignItems: "center" },
  iconWrap: { marginBottom: 16 },
  title: { color: "#FFFFFF", fontSize: 24, fontWeight: "700", textAlign: "center", marginBottom: 12 },
  body: { color: "#CCC", fontSize: 15, textAlign: "center", lineHeight: 22, marginTop: 12 },
  button: {
    backgroundColor: "#4ADE80",
    borderRadius: 16,
    paddingVertical: 14,
    paddingHorizontal: 32,
    marginTop: 32,
  },
  buttonText: { color: "#0F0F0F", fontSize: 16, fontWeight: "700" },
});
