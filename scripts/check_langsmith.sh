#!/bin/bash
# Hook: Verifica conectividad con LangSmith antes de ejecutar el servidor.
# Se ejecuta como PreToolUse en Bash cuando se detecta uvicorn.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Solo correr si el comando incluye uvicorn (arranque del servidor)
if [[ "$COMMAND" != *"uvicorn"* ]]; then
  exit 0
fi

cd /Users/jpozoc/Documents/contador-macros/backend

# Verificar que existe .env
if [ ! -f .env ]; then
  echo "⚠️  No existe backend/.env — copia .env.example y configura tus API keys."
  exit 0
fi

# Verificar variable GOOGLE_API_KEY
source <(grep -E '^(GOOGLE_API_KEY|LANGSMITH_API_KEY)=' .env 2>/dev/null || true)

if [ -z "${GOOGLE_API_KEY:-}" ]; then
  echo "⚠️  GOOGLE_API_KEY no configurada en .env — el endpoint /analyze no funcionará."
fi

if [ -z "${LANGSMITH_API_KEY:-}" ]; then
  echo "ℹ️  LANGSMITH_API_KEY no configurada — tracing deshabilitado."
  exit 0
fi

echo "🔍 Verificando conexión con LangSmith..."
python3 -c "
import langsmith
import os
os.environ['LANGCHAIN_API_KEY'] = '${LANGSMITH_API_KEY}'
client = langsmith.Client()
projects = list(client.list_projects())
print(f'✅ LangSmith conectado — {len(projects)} proyecto(s) encontrado(s).')
" 2>&1 || echo "⚠️  No se pudo conectar a LangSmith. Verifica LANGSMITH_API_KEY."
