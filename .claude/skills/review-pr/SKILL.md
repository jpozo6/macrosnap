---
name: review-pr
description: Revisa el código del PR actual o un PR específico por número. Usar cuando se pide revisar un PR o antes de hacer merge.
context: fork
agent: Explore
allowed-tools: Bash(git *) Bash(gh *)
---

Realiza una revisión completa del código del Pull Request $ARGUMENTS.

Si no se indica número, revisa los cambios de la rama actual respecto a main.

## 1. Resumen
- Qué hace este PR en 2-3 frases
- Archivos modificados y líneas cambiadas

## 2. Análisis de calidad
Para cada archivo modificado evalúa:
- Legibilidad (nombres, estructura)
- Complejidad ciclomática (flag si > 10)
- Duplicación de código
- Manejo de errores
- Type safety

## 3. Problemas encontrados
Clasifica cada problema como:
- CRITICAL: Bugs, vulnerabilidades, pérdida de datos
- WARNING: Code smells, rendimiento subóptimo
- SUGGESTION: Mejoras opcionales de estilo

## 4. Tests
- ¿Se añadieron tests para los cambios?
- Sugerencias de tests que faltan

## 5. Veredicto
APPROVE / REQUEST_CHANGES / COMMENT con lista de cambios necesarios

Ejecuta: git log main..HEAD --oneline y git diff main...HEAD