/** Hook para gestión de cámara y permisos. */

import { useState, useCallback } from "react";
import { Platform } from "react-native";

function useWebCamera() {
  const [photo, setPhoto] = useState<string | null>(null);

  const requestPermission = useCallback(async () => true, []);

  const pickFromGallery = useCallback(async (): Promise<string | null> => {
    return new Promise((resolve) => {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = "image/*";
      input.onchange = (e) => {
        const file = (e.target as HTMLInputElement).files?.[0];
        if (file) {
          const uri = URL.createObjectURL(file);
          setPhoto(uri);
          resolve(uri);
        } else {
          resolve(null);
        }
      };
      input.click();
    });
  }, []);

  const takePhoto = useCallback(
    async (_cameraRef: unknown): Promise<string> => {
      // En web, captura de cámara usa el mismo file picker con capture
      return new Promise((resolve) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.setAttribute("capture", "environment");
        input.onchange = (e) => {
          const file = (e.target as HTMLInputElement).files?.[0];
          if (file) {
            const uri = URL.createObjectURL(file);
            setPhoto(uri);
            resolve(uri);
          }
        };
        input.click();
      });
    },
    []
  );

  const clearPhoto = useCallback(() => {
    setPhoto(null);
  }, []);

  return {
    photo,
    hasPermission: true as boolean | null,
    requestPermission,
    takePhoto,
    pickFromGallery,
    clearPhoto,
  };
}

function useNativeCamera() {
  const [photo, setPhoto] = useState<string | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  const requestPermission = useCallback(async () => {
    const { Camera } = await import("expo-camera");
    const { status } = await Camera.requestCameraPermissionsAsync();
    setHasPermission(status === "granted");
    return status === "granted";
  }, []);

  const takePhoto = useCallback(
    async (cameraRef: { takePictureAsync: (opts?: Record<string, unknown>) => Promise<{ uri: string }> }) => {
      const result = await cameraRef.takePictureAsync({
        quality: 0.8,
        base64: false,
      });
      setPhoto(result.uri);
      return result.uri;
    },
    []
  );

  const pickFromGallery = useCallback(async () => {
    const ImagePicker = await import("expo-image-picker");
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      const uri = result.assets[0].uri;
      setPhoto(uri);
      return uri;
    }
    return null;
  }, []);

  const clearPhoto = useCallback(() => {
    setPhoto(null);
  }, []);

  return {
    photo,
    hasPermission,
    requestPermission,
    takePhoto,
    pickFromGallery,
    clearPhoto,
  };
}

export const useCamera = Platform.OS === "web" ? useWebCamera : useNativeCamera;
