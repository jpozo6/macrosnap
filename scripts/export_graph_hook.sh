#!/bin/bash
# Hook: Regenera la visualización del grafo cuando se modifican archivos de chain/.
# Se ejecuta como PostToolUse en Edit/Write.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null || echo "")

# Solo correr si se editó un archivo dentro de chain/
if [[ "$FILE_PATH" != *"backend/app/chain/"* ]]; then
  exit 0
fi

cd /Users/jpozoc/Documents/contador-macros

echo "🔄 Regenerando visualización del grafo LangGraph..."
python3 scripts/export_graph.py 2>&1
