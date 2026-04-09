---
name: commit
description: Genera un mensaje de commit semántico analizando los cambios staged
disable-model-invocation: true
allowed-tools: Bash(git *)
---

Analiza los cambios staged en git (git diff --staged) y genera un mensaje de commit
siguiendo la convención Conventional Commits:

Formato obligatorio:
- tipo(scope): descripcion breve (max 72 caracteres)
- Línea en blanco
- Cuerpo descriptivo explicando el "por qué" (no el "qué")
- Footer con breaking changes si aplica

Tipos permitidos: feat, fix, docs, style, refactor, perf, test, build, ci, chore

Reglas:
1. Analiza TODOS los archivos modificados, no solo el primero
2. Si hay más de 3 archivos en diferentes módulos, sugiere dividir en commits
3. El scope debe ser el módulo o directorio principal afectado
4. Usa imperativo: "Añade", "Corrige", "Elimina"
5. Si detectas un breaking change, incluye "BREAKING CHANGE:" en el footer

Ejecuta: git status y git diff --staged
Luego propón el mensaje y pide confirmación antes de hacer el commit.