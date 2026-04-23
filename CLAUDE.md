# MacroSnap - Guía de desarrollo

## Comandos

### Backend
- `cd backend && pip install -r requirements.txt` — instalar dependencias
- `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` — run dev server
- `cd backend && python -m pytest tests/ -v` — tests

### Mobile
- `cd mobile && npm install` — instalar dependencias
- `cd mobile && npx expo start` — iniciar dev server
- `cd mobile && npx expo run:ios` — run en iOS
- `cd mobile && npx expo run:android` — run en Android

## Arquitectura

El pipeline de análisis usa LangGraph con 3 nodos:
1. **identify_food** — Gemini Flash identifica los alimentos en la imagen
2. **estimate_portions** — Estima porciones/cantidades de cada alimento
3. **calculate_macros** — Calcula macronutrientes (kcal, proteína, carbohidratos, grasa, fibra)

Cada ejecución del grafo se tracéa automáticamente en LangSmith.

## Variables de entorno requeridas (backend/.env)
- GOOGLE_API_KEY — API key de Google AI (Gemini)
- LANGSMITH_API_KEY — API key de LangSmith
- LANGSMITH_PROJECT — Nombre del proyecto en LangSmith
- DATABASE_URL — URL de la base de datos (default: sqlite:///./macrosnap.db)

### Auth (JWT + verificación email)
- SECRET_KEY — string largo aleatorio para firmar los JWT (obligatorio en producción)
- ACCESS_TOKEN_EXPIRE_MINUTES — minutos de vida del JWT (default 10080 = 7 días)
- VERIFICATION_TOKEN_EXPIRE_HOURS — horas de vida del token de verificación (default 24)
- FRONTEND_URL — URL pública del frontend para construir el enlace de verificación
  (dev local: `http://localhost:8081`, prod web: `http://<tu-host>`)

### SMTP (envío de emails de verificación, provider-agnostic)
- SMTP_HOST — p.ej. `smtp.gmail.com`, `smtp.resend.com`, `smtp.sendgrid.net`
- SMTP_PORT — 587 (STARTTLS) o 465 (TLS directo)
- SMTP_USER — usuario/login del proveedor
- SMTP_PASSWORD — password o API key (Gmail: App Password; Resend: `re_xxx`)
- SMTP_FROM — email emisor (debe estar autorizado por el proveedor)
- SMTP_FROM_NAME — nombre visible (default `MacroSnap`)
- SMTP_START_TLS — `true` para puerto 587 (default), `false` para 465
- SMTP_USE_TLS — `true` solo si `SMTP_START_TLS=false` y el puerto usa TLS directo

Si `SMTP_HOST` o `SMTP_FROM` están vacíos, el envío se desactiva y se loguea el
contenido del email (útil en desarrollo).

## Autenticación
- JWT propio firmado con HS256 (`SECRET_KEY`).
- Registro exige email + confirmación de email + password (≥8 caracteres); el email
  se normaliza a minúsculas y debe ser único.
- Tras `/auth/register` se envía email con token; `/auth/verify-email?token=...`
  marca la cuenta como verificada. El login falla con 403 si el email no está verificado.
- Token JWT en `Authorization: Bearer <token>`. En mobile se guarda en
  `expo-secure-store` (nativo) o `localStorage` (web).
- Todas las rutas de `/meals` y `/analyze` requieren usuario autenticado; los meals
  están filtrados por `user_id`.

## Tests
- `cd backend && python -m pytest tests/ -v` — ejecutar todos los tests (97 tests)
- `cd backend && python -m pytest tests/test_chain_nodes.py -v` — solo tests de nodos/parsing
- `cd backend && python -m pytest tests/test_routers_meals.py -v` — solo tests de endpoints meals
- Los tests usan SQLite in-memory, no requieren API keys ni servicios externos
- Los nodos de LangGraph se testean con mocks del LLM (no llaman a Gemini)

## CI / GitHub Actions
- El workflow `.github/workflows/ci.yml` ejecuta tests y validadores en cada push/PR a main
- Matriz de Python 3.11 y 3.12

## Hooks de validación
Los hooks de Claude Code (`.claude/hooks/`) ejecutan validaciones automáticas:
- **Pre-commit**: API keys, seguridad, prompts, schema de macros, grafo, type hints, migraciones
- **Pre-push**: todo lo anterior + tests completos + validación estricta
- **Post-edit**: validación contextual al modificar archivos del pipeline

## Convenciones
- Backend: Python 3.11+, type hints obligatorios, docstrings en español
- Mobile: TypeScript estricto, componentes funcionales, hooks custom para lógica reutilizable
- Commits: conventional commits en español (feat:, fix:, refactor:, etc.)
- Nunca hardcodear API keys, siempre .env
