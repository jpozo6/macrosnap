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

## Convenciones
- Backend: Python 3.11+, type hints obligatorios, docstrings en español
- Mobile: TypeScript estricto, componentes funcionales, hooks custom para lógica reutilizable
- Commits: conventional commits en español (feat:, fix:, refactor:, etc.)
- Nunca hardcodear API keys, siempre .env
