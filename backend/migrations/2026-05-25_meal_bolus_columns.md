# 2026-05-25 — Columnas de bolo de insulina en `meals`

PR 2/4 del pivot a diabéticos. Añade 8 columnas nullable en `meals` para
guardar, junto a cada comida, los datos del bolo de insulina que el usuario
decidió administrarse.

## Cambios

Columnas nuevas en `meals` (todas nullable, sin defaults complejos):

- `glucose_mg_dl` (`INTEGER`) — glucemia capilar del usuario al momento del bolo
- `exercise_level` (`VARCHAR(20)`) — `none` / `moderate` / `intense`
- `slot` (`VARCHAR(20)`) — `breakfast` / `lunch` / `dinner`
- `rations_hc` (`FLOAT`) — raciones de HC = `carbs_g / ration_grams`
- `bolus_carb_units` (`FLOAT`) — componente del bolo por HC
- `bolus_correction_units` (`FLOAT`) — componente de corrección
- `bolus_suggested_units` (`FLOAT`) — lo que la app sugirió
- `bolus_total_units` (`FLOAT`) — lo que el usuario finalmente administró

## Impacto en producción

`backend/app/migrations.py::apply_missing_columns()` ya aplica estos `ALTER
TABLE ADD COLUMN` de forma idempotente en cada arranque del backend, así
que el deploy lo resuelve solo: el shim añadido en `c44ce97` se ha ampliado
con la sub-lista `_meals_migrations(...)`.

Los registros existentes mantienen todos los campos nuevos a `NULL`. Las
comidas sin bolo registrado (de usuarios no diabéticos o anteriores al
PR 2) se siguen leyendo con normalidad: el helper `_meal_bolus_data` del
router devuelve `None` cuando `bolus_total_units IS NULL`, y
`MealResponse.bolus` es `BolusData | None`.

## Rollback

```sql
ALTER TABLE meals DROP COLUMN glucose_mg_dl;
ALTER TABLE meals DROP COLUMN exercise_level;
ALTER TABLE meals DROP COLUMN slot;
ALTER TABLE meals DROP COLUMN rations_hc;
ALTER TABLE meals DROP COLUMN bolus_carb_units;
ALTER TABLE meals DROP COLUMN bolus_correction_units;
ALTER TABLE meals DROP COLUMN bolus_suggested_units;
ALTER TABLE meals DROP COLUMN bolus_total_units;
```

Solo afecta a meals; ni `users` ni `diabetic_profiles` se tocan.
