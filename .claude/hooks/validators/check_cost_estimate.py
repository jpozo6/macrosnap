#!/usr/bin/env python3
"""Estima coste por llamada a Gemini Flash y alerta si supera umbral."""

import re
import sys
from pathlib import Path

# Pricing Gemini 1.5 Flash (USD por 1M tokens) — actualizar según pricing vigente
INPUT_COST_PER_M_TOKENS = 0.075   # $0.075 por 1M input tokens
OUTPUT_COST_PER_M_TOKENS = 0.30   # $0.30 por 1M output tokens
IMAGE_TOKENS_ESTIMATE = 258       # Tokens estimados por imagen en Gemini Flash

# Umbral de alerta por llamada completa al pipeline (3 nodos)
COST_ALERT_THRESHOLD_USD = 0.01   # $0.01 por ejecución completa del pipeline

PROMPTS_FILE = Path("backend/app/chain/prompts.py")


def estimate_tokens(text: str) -> int:
    """Estimación burda: ~4 caracteres por token."""
    return len(text) // 4


def main() -> int:
    if not PROMPTS_FILE.exists():
        return 0

    content = PROMPTS_FILE.read_text(encoding="utf-8")

    # Extraer todos los prompts
    prompts = re.findall(r'"""(.*?)"""', content, re.DOTALL)

    total_input_tokens = 0
    total_output_tokens = 0

    for prompt in prompts:
        input_tokens = estimate_tokens(prompt)
        output_tokens = 200  # Estimación de respuesta JSON típica
        total_input_tokens += input_tokens
        total_output_tokens += output_tokens

    # Añadir tokens de imagen (solo el primer nodo usa imagen)
    total_input_tokens += IMAGE_TOKENS_ESTIMATE

    # Calcular coste estimado
    input_cost = (total_input_tokens / 1_000_000) * INPUT_COST_PER_M_TOKENS
    output_cost = (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_M_TOKENS
    total_cost = input_cost + output_cost

    if total_cost > COST_ALERT_THRESHOLD_USD:
        print(f"⚠️ Coste estimado por ejecución del pipeline: ${total_cost:.4f}")
        print(f"   Input: ~{total_input_tokens} tokens (${input_cost:.5f})")
        print(f"   Output: ~{total_output_tokens} tokens (${output_cost:.5f})")
        print(f"   Imagen: ~{IMAGE_TOKENS_ESTIMATE} tokens")
        print(f"   Umbral configurado: ${COST_ALERT_THRESHOLD_USD}")
        print("   Considera optimizar los prompts o reducir el detalle del JSON de respuesta.")
        return 1

    # Siempre informar el coste estimado (sin bloquear)
    print(f"💰 Coste estimado por ejecución: ${total_cost:.4f} (umbral: ${COST_ALERT_THRESHOLD_USD})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
