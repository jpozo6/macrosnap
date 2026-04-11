/** Hook para enviar imagen al backend y recibir análisis de macros. */

import { useCallback } from "react";
import { analyzeImage } from "../services/api";
import { useMealStore } from "../store/useMealStore";

export function useAnalysis() {
  const {
    analysisStatus,
    analysisResult,
    analysisError,
    setAnalysisLoading,
    setAnalysisSuccess,
    setAnalysisError,
    resetAnalysis,
  } = useMealStore();

  const analyze = useCallback(
    async (imageUri: string, comment?: string) => {
      setAnalysisLoading();
      try {
        const result = await analyzeImage(imageUri, comment);
        setAnalysisSuccess(result);
        return result;
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Error desconocido al analizar";
        setAnalysisError(message);
        return null;
      }
    },
    [setAnalysisLoading, setAnalysisSuccess, setAnalysisError]
  );

  return {
    analyze,
    result: analysisResult,
    status: analysisStatus,
    error: analysisError,
    reset: resetAnalysis,
  };
}
