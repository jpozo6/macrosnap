"""Prompt templates para cada nodo del pipeline de análisis."""

IDENTIFY_FOODS_PROMPT = """Analiza esta imagen de comida. Lista cada alimento visible con su nivel de confianza (0.0 a 1.0).

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "foods": [
    {{"name": "nombre del alimento", "confidence": 0.95}},
    ...
  ],
  "meal_name": "nombre descriptivo corto del plato"
}}

Sé específico con los alimentos (ej: "arroz blanco" en vez de "arroz", "pechuga de pollo a la plancha" en vez de "pollo").
Si no puedes identificar alimentos en la imagen, responde con {{"foods": [], "meal_name": "No identificado"}}."""

ESTIMATE_PORTIONS_PROMPT = """Dada esta lista de alimentos identificados en una comida, estima las porciones en gramos basándote en porciones típicas de un plato individual.

Alimentos identificados:
{foods_list}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "portions": [
    {{"name": "nombre del alimento", "amount": 150, "unit": "g"}},
    ...
  ]
}}

Usa tu conocimiento sobre tamaños típicos de porciones. Si un alimento es una bebida, usa "ml" como unidad."""

CALCULATE_MACROS_PROMPT = """Calcula los macronutrientes totales de esta comida basándote en los alimentos y sus porciones.

Alimentos con porciones:
{portions_list}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "calories": 450,
  "protein_g": 30.5,
  "carbs_g": 45.2,
  "fat_g": 15.8,
  "fiber_g": 5.3
}}

Calcula los valores nutricionales lo más precisamente posible usando datos estándar de composición de alimentos. Los valores deben ser la SUMA TOTAL de todos los alimentos."""
