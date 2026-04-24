import { Stack } from "expo-router";

export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: "#0F0F0F" },
        headerTintColor: "#FFFFFF",
        contentStyle: { backgroundColor: "#0F0F0F" },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="login" options={{ title: "Iniciar sesión" }} />
      <Stack.Screen name="register" options={{ title: "Crear cuenta" }} />
      <Stack.Screen name="verify-pending" options={{ title: "Verifica tu email" }} />
      <Stack.Screen name="verify-email" options={{ title: "Verificación" }} />
      <Stack.Screen name="forgot-password" options={{ title: "Recuperar contraseña" }} />
      <Stack.Screen name="reset-password" options={{ title: "Nueva contraseña" }} />
    </Stack>
  );
}
