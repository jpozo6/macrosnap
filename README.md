# MacroSnap

App de tracking de macronutrientes por foto. Saca una foto de tu comida, la IA analiza los alimentos y calcula calorías, proteína, carbohidratos y grasa.

## Stack

- **Frontend**: React Native + Expo (SDK 52)
- **Backend**: FastAPI + LangGraph + Gemini Flash
- **Observabilidad**: LangSmith
- **Base de datos**: SQLite (MVP)

## Setup rápido

### Backend

```bash
cd backend
cp .env.example .env
# Edita .env con tus API keys

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará en http://localhost:8000. Docs en http://localhost:8000/docs.

### Mobile

```bash
cd mobile
npm install
npx expo start
```

Escanea el QR con Expo Go o presiona `i` para iOS / `a` para Android.

### Variables de entorno

| Variable | Descripción |
|---|---|
| `GOOGLE_API_KEY` | API key de Google AI (Gemini Flash) |
| `LANGSMITH_API_KEY` | API key de LangSmith (opcional) |
| `LANGSMITH_PROJECT` | Nombre del proyecto en LangSmith |
| `DATABASE_URL` | URL de la base de datos |

## Pipeline de análisis

El análisis usa LangGraph con 3 nodos secuenciales:

1. **identify_food** — Gemini Flash identifica alimentos en la imagen (visión multimodal)
2. **estimate_portions** — Estima cantidades en gramos
3. **calculate_macros** — Calcula macronutrientes totales

Cada ejecución genera un trace automático en LangSmith.

## API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/analyze` | Analiza imagen de comida |
| GET | `/api/v1/meals` | Lista histórico de comidas |
| GET | `/api/v1/meals/:id` | Detalle de una comida |
| DELETE | `/api/v1/meals/:id` | Elimina una comida |
| GET | `/api/v1/meals/summary/daily` | Resumen diario de macros |
| GET | `/health` | Health check |
