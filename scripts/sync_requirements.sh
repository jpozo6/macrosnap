#!/bin/bash
# Hook: Sincroniza dependencias cuando se modifica requirements.txt.
# Se ejecuta como PostToolUse en Edit/Write.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Solo correr si se editó requirements.txt
if [[ "$FILE_PATH" != *"requirements.txt" ]]; then
  exit 0
fi

cd /Users/jpozoc/Documents/contador-macros/backend

echo "📦 Sincronizando dependencias..."
pip install -r requirements.txt --quiet 2>&1 | tail -5
echo "✅ Dependencias actualizadas."
