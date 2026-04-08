#!/bin/bash
# Hook: Verifica tipado con mypy tras editar archivos .py del backend.
# Se ejecuta como PostToolUse en Edit/Write. Recibe JSON del tool use en stdin.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Solo correr si el archivo editado es .py dentro de backend/
if [[ "$FILE_PATH" != *"backend/"*".py" ]]; then
  exit 0
fi

cd /Users/jpozoc/Documents/contador-macros/backend

echo "🔍 Verificando tipado con mypy..."
python3 -m mypy app/ --ignore-missing-imports --no-error-summary 2>&1 | tail -10

EXIT_CODE=${PIPESTATUS[0]}
if [ "$EXIT_CODE" -ne 0 ]; then
  echo "❌ mypy encontró errores de tipado. Corrígelos antes de continuar."
fi
exit "$EXIT_CODE"
