#!/bin/bash
# Guard para ediciones: valida consistencia al modificar archivos críticos del pipeline.
# Se invoca como hook de Claude Code (PostToolUse en Edit|Write).

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path', d.get('tool_response',{}).get('filePath','')))" 2>/dev/null || echo "")

HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATORS_DIR="$HOOKS_DIR/validators"

case "$FILE_PATH" in
    *"/chain/prompts.py")
        echo "🔍 Archivo de prompts modificado — validando..."
        python3 "$VALIDATORS_DIR/check_prompts.py" 2>&1 || true
        python3 "$VALIDATORS_DIR/check_cost_estimate.py" 2>&1 || true
        ;;
    *"/schemas.py"|*"/chain/state.py"|*"/models.py")
        echo "🔍 Schema/modelo modificado — verificando consistencia..."
        python3 "$VALIDATORS_DIR/check_macro_schema.py" 2>&1 || true
        ;;
    *"/chain/graph.py")
        echo "🔍 Grafo LangGraph modificado — verificando estructura..."
        python3 "$VALIDATORS_DIR/check_langgraph.py" 2>&1 || true
        ;;
    *"/chain/nodes.py")
        echo "🔍 Nodos modificados — verificando parsing y schema..."
        python3 "$VALIDATORS_DIR/check_parse_tests.py" 2>&1 || true
        python3 "$VALIDATORS_DIR/check_macro_schema.py" 2>&1 || true
        ;;
    *"/services/langsmith.py")
        echo "🔍 Config LangSmith modificada — verificando trazabilidad..."
        python3 "$VALIDATORS_DIR/check_langsmith_tracing.py" 2>&1 || true
        ;;
    *"/routers/analysis.py")
        echo "🔍 Router de análisis modificado — verificando validación de imágenes..."
        python3 "$VALIDATORS_DIR/check_image_validation.py" 2>&1 || true
        ;;
esac

exit 0
