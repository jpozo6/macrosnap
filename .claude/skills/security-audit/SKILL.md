---
name: security-audit
description: Auditoría de seguridad completa del proyecto. Usar cuando se pide revisar seguridad, vulnerabilidades o antes de un release.
context: fork
agent: Explore
allowed-tools: Bash(npm *) Bash(grep *) Read Grep Glob
---

Realiza una auditoría de seguridad exhaustiva del proyecto.

## Dependencias
- Ejecuta: npm audit / pip audit
- Revisa dependencias con vulnerabilidades conocidas (CVEs)
- Identifica dependencias desactualizadas (más de 6 meses)

## Secretos y credenciales
- Busca: API keys, tokens, contraseñas hardcodeadas
- Revisa: .env files no gitignored, archivos de configuración
- Verifica: .gitignore incluye .env, credentials, *.pem, *.key

## Inputs y validación
- Busca: SQL injection, XSS, command injection
- Revisa: validación de inputs en endpoints/formularios
- Verifica: sanitización de datos antes de renderizar

## Autenticación y autorización
- Revisa: manejo de sesiones y tokens JWT
- Verifica: rutas protegidas con middleware de auth
- Busca: endpoints sin autenticación que deberían tenerla

## Configuración
- Revisa: headers de seguridad (CORS, CSP, HSTS)
- Verifica: configuración de producción vs desarrollo
- Busca: debug mode habilitado, verbose logging en prod

Genera reporte con severidad: CRITICAL / HIGH / MEDIUM / LOW / INFO
Ordena por severidad descendente.