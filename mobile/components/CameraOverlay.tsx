/** UI overlay sobre la cámara con botones de captura y galería. */

import { View, TouchableOpacity, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

interface CameraOverlayProps {
  onCapture: () => void;
  onGallery: () => void;
}

export function CameraOverlay({ onCapture, onGallery }: CameraOverlayProps) {
  return (
    <View style={styles.container}>
      <View style={styles.topBar} />
      <View style={styles.bottomBar}>
        <TouchableOpacity style={styles.galleryButton} onPress={onGallery}>
          <Ionicons name="images" size={28} color="#FFFFFF" />
        </TouchableOpacity>
        <TouchableOpacity style={styles.captureButton} onPress={onCapture}>
          <View style={styles.captureInner} />
        </TouchableOpacity>
        <View style={styles.placeholder} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: "space-between",
  },
  topBar: {
    height: 100,
    backgroundColor: "rgba(0,0,0,0.3)",
  },
  bottomBar: {
    height: 120,
    backgroundColor: "rgba(0,0,0,0.5)",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    paddingHorizontal: 30,
  },
  galleryButton: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.15)",
    alignItems: "center",
    justifyContent: "center",
  },
  captureButton: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 4,
    borderColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
  },
  captureInner: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: "#FFFFFF",
  },
  placeholder: {
    width: 48,
  },
});
