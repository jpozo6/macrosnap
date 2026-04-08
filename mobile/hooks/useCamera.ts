/** Hook para gestión de cámara y permisos. */

import { useState, useCallback } from "react";
import { Camera } from "expo-camera";
import * as ImagePicker from "expo-image-picker";

export function useCamera() {
  const [photo, setPhoto] = useState<string | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);

  const requestPermission = useCallback(async () => {
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
