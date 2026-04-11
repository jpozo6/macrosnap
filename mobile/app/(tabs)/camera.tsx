/** Pantalla principal: captura foto de comida. */

import { useRef, useEffect, useState } from "react";
import {
  View,
  Text,
  Image,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  StyleSheet,
  ActivityIndicator,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { CameraView } from "expo-camera";
import { useRouter } from "expo-router";
import { useCamera } from "../../hooks/useCamera";
import { useAnalysis } from "../../hooks/useAnalysis";
import { CameraOverlay } from "../../components/CameraOverlay";

export default function CameraScreen() {
  const router = useRouter();
  const cameraRef = useRef<CameraView>(null);
  const { photo, hasPermission, requestPermission, takePhoto, pickFromGallery, clearPhoto } =
    useCamera();
  const { analyze, status } = useAnalysis();
  const [showPreview, setShowPreview] = useState(false);
  const [comment, setComment] = useState("");

  useEffect(() => {
    requestPermission();
  }, [requestPermission]);

  const handleCapture = async () => {
    if (cameraRef.current) {
      await takePhoto(cameraRef.current);
      setShowPreview(true);
    }
  };

  const handleGallery = async () => {
    const uri = await pickFromGallery();
    if (uri) {
      setShowPreview(true);
    }
  };

  const handleRetry = () => {
    clearPhoto();
    setShowPreview(false);
    setComment("");
  };

  const handleAnalyze = async () => {
    if (!photo) return;
    const result = await analyze(photo, comment || undefined);
    if (result) {
      setShowPreview(false);
      clearPhoto();
      setComment("");
      router.push(`/result/${result.meal_id}`);
    }
  };

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#4ADE80" />
      </View>
    );
  }

  if (!hasPermission) {
    return (
      <View style={styles.container}>
        <Text style={styles.permissionText}>
          MacroSnap necesita acceso a la cámara para funcionar
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>Dar permisos</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Preview de la foto capturada
  if (showPreview && photo) {
    return (
      <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
        <KeyboardAvoidingView
          style={styles.previewContainer}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
          keyboardVerticalOffset={Platform.OS === "ios" ? 60 : 0}
        >
          <Image source={{ uri: photo }} style={styles.previewImage} />
          {status === "loading" ? (
            <View style={styles.loadingOverlay}>
              <ActivityIndicator size="large" color="#4ADE80" />
              <Text style={styles.loadingText}>Analizando tu comida...</Text>
            </View>
          ) : (
            <View style={styles.previewBottom}>
              <TextInput
                style={styles.commentInput}
                placeholder="Ej: 200g de pechuga, arroz integral..."
                placeholderTextColor="#666"
                value={comment}
                onChangeText={setComment}
                multiline
                maxLength={300}
                returnKeyType="done"
                blurOnSubmit
              />
              <View style={styles.previewActions}>
                <TouchableOpacity style={styles.retryButton} onPress={handleRetry}>
                  <Text style={styles.buttonText}>Repetir</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.analyzeButton} onPress={handleAnalyze}>
                  <Text style={styles.analyzeButtonText}>Analizar</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
          {status === "error" && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>Error al analizar. Intenta de nuevo.</Text>
            </View>
          )}
        </KeyboardAvoidingView>
      </TouchableWithoutFeedback>
    );
  }

  // Vista de cámara
  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera} facing="back">
        <CameraOverlay onCapture={handleCapture} onGallery={handleGallery} />
      </CameraView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F0F0F",
    justifyContent: "center",
    alignItems: "center",
  },
  previewContainer: {
    flex: 1,
    backgroundColor: "#0F0F0F",
  },
  camera: {
    flex: 1,
    width: "100%",
  },
  previewImage: {
    flex: 1,
    width: "100%",
    resizeMode: "cover",
  },
  previewBottom: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
    backgroundColor: "#0F0F0F",
  },
  commentInput: {
    backgroundColor: "rgba(26,26,26,0.9)",
    color: "#FFFFFF",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 15,
    height: 48,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.1)",
  },
  previewActions: {
    flexDirection: "row",
    gap: 20,
  },
  retryButton: {
    flex: 1,
    height: 52,
    justifyContent: "center",
    borderRadius: 16,
    backgroundColor: "#1A1A1A",
    alignItems: "center",
  },
  analyzeButton: {
    flex: 1,
    height: 52,
    justifyContent: "center",
    borderRadius: 16,
    backgroundColor: "#4ADE80",
    alignItems: "center",
  },
  buttonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  analyzeButtonText: {
    color: "#0F0F0F",
    fontSize: 16,
    fontWeight: "700",
  },
  loadingOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(15,15,15,0.8)",
    justifyContent: "center",
    alignItems: "center",
    gap: 16,
  },
  loadingText: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "500",
  },
  errorBanner: {
    position: "absolute",
    top: 60,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#EF4444",
  },
  errorText: {
    color: "#FFFFFF",
    textAlign: "center",
    fontWeight: "500",
  },
  permissionText: {
    color: "#FFFFFF",
    fontSize: 16,
    textAlign: "center",
    paddingHorizontal: 40,
    marginBottom: 20,
  },
  permissionButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: "#4ADE80",
  },
  permissionButtonText: {
    color: "#0F0F0F",
    fontWeight: "700",
    fontSize: 16,
  },
});
