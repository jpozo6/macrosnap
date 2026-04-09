#!/bin/bash
# Pre-commit hook: ejecuta todas las validaciones antes de permitir git commit.
# Se invoca como hook de Claude Code (PreToolUse en Bash, filtrado con if: "Bash(git commit*)").

set -euo pipefail

HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATORS_DIR="$HOOKS_DIR/validators"
ERRORS=""
WARNINGS=""

echo "🔍 Ejecutando validaciones pre-commit..."

# --- Validaciones críticas (bloquean el commit) ---

# 1. API keys hardcodeadas
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_api_keys.py" 2>&1); then
    echo "  ✓ API keys"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 2. Archivos .env
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_env_files.py" 2>&1); then
    echo "  ✓ Archivos .env"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 3. Seguridad básica
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_security.py" 2>&1); then
    echo "  ✓ Seguridad"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 4. Validación de prompts LLM
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_prompts.py" 2>&1); then
    echo "  ✓ Prompts LLM"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 5. Consistencia de schema de macros
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_macro_schema.py" 2>&1); then
    echo "  ✓ Schema de macros"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 6. Lint del grafo LangGraph
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_langgraph.py" 2>&1); then
    echo "  ✓ Grafo LangGraph"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 7. Type hints
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_types.py" 2>&1); then
    echo "  ✓ Type hints"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# 8. Migraciones de BD
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_migrations.py" 2>&1); then
    echo "  ✓ Migraciones DB"
else
    ERRORS="$ERRORS\n$OUTPUT"
fi

# --- Validaciones informativas (warnings, no bloquean) ---

# 9. Rangos de macros razonables
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_macro_ranges.py" 2>&1); then
    echo "  ✓ Rangos de macros"
else
    WARNINGS="$WARNINGS\n$OUTPUT"
fi

# 10. Trazabilidad LangSmith
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_langsmith_tracing.py" 2>&1); then
    echo "  ✓ Trazabilidad LangSmith"
else
    WARNINGS="$WARNINGS\n$OUTPUT"
fi

# 11. Validación de imágenes
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_image_validation.py" 2>&1); then
    echo "  ✓ Validación de imágenes"
else
    WARNINGS="$WARNINGS\n$OUTPUT"
fi

# 12. Tests de parsing
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_parse_tests.py" 2>&1); then
    echo "  ✓ Tests de parsing"
else
    WARNINGS="$WARNINGS\n$OUTPUT"
fi

# 13. Coste estimado (siempre informativo)
OUTPUT=$(python3 "$VALIDATORS_DIR/check_cost_estimate.py" 2>&1) || true
echo "  $OUTPUT"

# --- Resultado final ---

if [ -n "$WARNINGS" ]; then
    echo ""
    echo "⚠️  Warnings (no bloquean el commit):"
    echo -e "$WARNINGS"
fi

if [ -n "$ERRORS" ]; then
    echo ""
    echo -e "$ERRORS"
    echo '{"decision":"block","reason":"Pre-commit: errores críticos detectados. Revisa los mensajes anteriores."}'
    exit 2
fi

echo ""
echo "✅ Todas las validaciones pre-commit pasaron."
exit 0
