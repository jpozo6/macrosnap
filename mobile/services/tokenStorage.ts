/** Persistencia del JWT entre sesiones.
 *
 * Usa expo-secure-store en nativo (keychain/keystore) y localStorage en web. */

import { Platform } from "react-native";

const KEY = "macrosnap_auth_token";

export async function saveToken(token: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.setItem(KEY, token);
    return;
  }
  const SecureStore = await import("expo-secure-store");
  await SecureStore.setItemAsync(KEY, token);
}

export async function getToken(): Promise<string | null> {
  if (Platform.OS === "web") {
    return localStorage.getItem(KEY);
  }
  const SecureStore = await import("expo-secure-store");
  return SecureStore.getItemAsync(KEY);
}

export async function clearToken(): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.removeItem(KEY);
    return;
  }
  const SecureStore = await import("expo-secure-store");
  await SecureStore.deleteItemAsync(KEY);
}
