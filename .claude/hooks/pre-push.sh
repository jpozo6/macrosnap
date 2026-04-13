#!/bin/bash
# Pre-push hook: validaciones estrictas antes de permitir git push.
# Se invoca como hook de Claude Code (PreToolUse en Bash).
# Filtra por stdin JSON: solo ejecuta si el comando es "git push*".

set -euo pipefail

# Leer stdin y verificar si el comando es git push
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [[ "$COMMAND" != git\ push* ]]; then
    exit 0
fi

HOOKS_DIR="$(cd "$(dirname "$0")" && pwd)"
VALIDATORS_DIR="$HOOKS_DIR/validators"
ERRORS=""

echo "🔍 Ejecutando validaciones pre-push..."

# 1. Todas las validaciones críticas
for validator in check_api_keys.py check_env_files.py check_security.py check_prompts.py \
                 check_macro_schema.py check_langgraph.py check_types.py check_migrations.py; do
    BASENAME="${validator%.py}"
    LABEL="${BASENAME#check_}"
    if OUTPUT=$(python3 "$VALIDATORS_DIR/$validator" 2>&1); then
        echo "  ✓ $LABEL"
    else
        ERRORS="$ERRORS\n$OUTPUT"
    fi
done

# 2. Validaciones que en pre-commit son warnings, aquí son bloqueantes (excepto image_validation que es aspiracional)
WARNINGS=""
for validator in check_macro_ranges.py check_langsmith_tracing.py check_parse_tests.py; do
    BASENAME="${validator%.py}"
    LABEL="${BASENAME#check_}"
    if OUTPUT=$(python3 "$VALIDATORS_DIR/$validator" 2>&1); then
        echo "  ✓ $LABEL"
    else
        ERRORS="$ERRORS\n$OUTPUT"
    fi
done

# Image validation es aspiracional — warning, no bloquea
if OUTPUT=$(python3 "$VALIDATORS_DIR/check_image_validation.py" 2>&1); then
    echo "  ✓ image_validation"
else
    WARNINGS="$WARNINGS\n$OUTPUT"
fi

# 3. Tests del proyecto (si existen)
if [ -d "backend/tests" ] && [ "$(find backend/tests -name '*.py' -not -name '__init__.py' 2>/dev/null | head -1)" ]; then
    echo "  ⏳ Ejecutando tests..."
    if OUTPUT=$(cd backend && python -m pytest tests/ -v --tb=short 2>&1); then
        echo "  ✓ Tests del proyecto"
    else
        ERRORS="$ERRORS\n❌ Tests fallidos:\n$OUTPUT"
    fi
else
    echo "  ⚠ No se encontraron tests en backend/tests/"
fi

# 4. Coste estimado (informativo)
OUTPUT=$(python3 "$VALIDATORS_DIR/check_cost_estimate.py" 2>&1) || true
echo "  $OUTPUT"

# --- Resultado final ---

if [ -n "$WARNINGS" ]; then
    echo ""
    echo "⚠️  Warnings:"
    echo -e "$WARNINGS"
fi

if [ -n "$ERRORS" ]; then
    echo ""
    echo -e "$ERRORS"
    echo '{"decision":"block","reason":"Pre-push: errores detectados. Corrige antes de pushear."}'
    exit 2
fi

echo ""
echo "✅ Todas las validaciones pre-push pasaron."
exit 0
