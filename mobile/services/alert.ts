/** Diálogos cross-platform.
 *
 * `Alert.alert` de react-native no está implementado en react-native-web,
 * por lo que los avisos de validación y errores quedaban silenciados en la
 * web y los botones parecían no responder. */

import { Alert, Platform } from "react-native";

export function showAlert(title: string, message?: string): void {
  if (Platform.OS === "web") {
    const text = message ? `${title}\n\n${message}` : title;
    if (typeof window !== "undefined" && typeof window.alert === "function") {
      window.alert(text);
    }
    return;
  }
  Alert.alert(title, message);
}

interface ConfirmOptions {
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
  onCancel?: () => void;
}

export function showConfirm(
  title: string,
  message: string,
  opts: ConfirmOptions,
): void {
  if (Platform.OS === "web") {
    const text = message ? `${title}\n\n${message}` : title;
    if (typeof window !== "undefined" && typeof window.confirm === "function") {
      if (window.confirm(text)) {
        opts.onConfirm();
      } else {
        opts.onCancel?.();
      }
    }
    return;
  }
  Alert.alert(title, message, [
    { text: opts.cancelLabel ?? "Cancelar", style: "cancel", onPress: opts.onCancel },
    {
      text: opts.confirmLabel ?? "Aceptar",
      style: opts.destructive ? "destructive" : "default",
      onPress: opts.onConfirm,
    },
  ]);
}
