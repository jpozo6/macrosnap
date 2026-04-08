#!/bin/bash
# Hook: Impide que se escriban API keys o secrets hardcodeados en el código.
# Se ejecuta como PreToolUse en Edit/Write.

set -euo pipefail

INPUT=$(cat)
NEW_STRING=$(echo "$INPUT" | python3 -c "
import json,sys
data = json.load(sys.stdin)
ti = data.get('tool_input',{})
# Para Edit: revisar new_string. Para Write: revisar content.
print(ti.get('new_string', ti.get('content', '')))
" 2>/dev/null || echo "")

FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Ignorar archivos de config/env que sí pueden tener keys
if [[ "$FILE_PATH" == *".env"* ]] || [[ "$FILE_PATH" == *".env.example"* ]] || [[ "$FILE_PATH" == *"settings"* ]]; then
  exit 0
fi

# Buscar patrones de secrets hardcodeados
if echo "$NEW_STRING" | grep -qiE '(AIza[0-9A-Za-z_-]{35}|sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{36}|AKIA[0-9A-Z]{16})'; then
  echo "🚨 BLOQUEADO: Se detectó una posible API key hardcodeada en $FILE_PATH"
  echo "Usa variables de entorno (.env) en vez de hardcodear secrets."
  exit 1
fi

exit 0
