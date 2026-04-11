# MacroSnap

App de tracking de macronutrientes por foto. Saca una foto de tu comida, la IA analiza los alimentos y calcula calorías, proteína, carbohidratos y grasa.

## Stack

- **Frontend**: React Native + Expo (SDK 52)
- **Backend**: FastAPI + LangGraph + Gemini Flash
- **Observabilidad**: LangSmith
- **Base de datos**: SQLite (MVP)

## Setup rápido

### 1. Prerrequisitos

- Python 3.11+
- Node.js 18+ y npm
- [Expo Go](https://expo.dev/go) instalado en tu móvil (o simulador iOS/Android)
- API key de [Google AI Studio](https://aistudio.google.com/apikey) (Gemini Flash)
- API key de [LangSmith](https://smith.langchain.com/) (opcional, para observabilidad)

### 2. Backend

```bash
cd backend

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
# venv\Scripts\activate        # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tus API keys (ver tabla abajo)

# Arrancar el servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará en http://localhost:8000. Documentación interactiva en http://localhost:8000/docs.

> Para desactivar el entorno virtual cuando termines: `deactivate`

### 3. Mobile

```bash
cd mobile
npm install
npx expo start
```

Escanea el QR con Expo Go o presiona `i` para iOS / `a` para Android.

> Asegúrate de que el móvil y el ordenador estén en la misma red WiFi.

### Variables de entorno (`backend/.env`)

| Variable | Descripción | Requerida |
|---|---|---|
| `GOOGLE_API_KEY` | API key de Google AI (Gemini Flash) | Sí |
| `LANGSMITH_API_KEY` | API key de LangSmith | No |
| `LANGSMITH_PROJECT` | Nombre del proyecto en LangSmith | No |
| `DATABASE_URL` | URL de la base de datos (default: SQLite local) | No |

### Tests

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

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
