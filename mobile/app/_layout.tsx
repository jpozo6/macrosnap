import { Stack, useRouter, useSegments } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";
import { useAuthStore } from "../store/useAuthStore";

export default function RootLayout() {
  const { isInitialized, token, initialize } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    void initialize();
  }, [initialize]);

  useEffect(() => {
    if (!isInitialized) return;
    const inAuthGroup = segments[0] === "(auth)";
    if (!token && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (token && inAuthGroup) {
      router.replace("/(tabs)/camera");
    }
  }, [isInitialized, token, segments, router]);

  if (!isInitialized) {
    return (
      <View style={{ flex: 1, backgroundColor: "#0F0F0F", justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator color="#4ADE80" />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: "#0F0F0F" },
          headerTintColor: "#FFFFFF",
          contentStyle: { backgroundColor: "#0F0F0F" },
        }}
      >
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="result/[id]"
          options={{
            title: "Resultado",
            presentation: "modal",
          }}
        />
        <Stack.Screen
          name="bolus/[mealId]"
          options={{
            title: "Calcular bolo",
            presentation: "modal",
          }}
        />
      </Stack>
    </>
  );
}
