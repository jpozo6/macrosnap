# 2026-05-25 — Tabla `diabetic_profiles`

Primer paso del pivot a app para diabéticos (PR 1/4). Crea una tabla nueva
1:1 con `users` que almacena el perfil clínico del paciente y sus ratios
por franja horaria.

## Cambios

- Nueva tabla `diabetic_profiles` con columnas:
  - `id` PK, `user_id` FK→users (unique, indexada)
  - Generales: `ration_grams`, `target_glucose`, `hypo_threshold`,
    `bolus_rounding_step`
  - Ajuste por ejercicio: `exercise_moderate_factor`, `exercise_intense_factor`
  - Ratios por franja (desayuno / comida / cena): `ipr_{slot}`, `isf_{slot}`
  - Timestamps: `created_at`, `updated_at`

## Impacto en producción

`Base.metadata.create_all(bind=engine)` se encarga de crear la tabla en el
arranque del backend (igual que se hizo con `users` en su día). No hay
backfill: la tabla nace vacía y solo se llena cuando un usuario activa el
modo diabético desde la UI (PR 3/4).

No requiere ningún `ALTER TABLE` manual ni cambios en tablas existentes,
así que el shim `apply_missing_columns` (introducido en `c44ce97`) no
necesita ampliarse para este PR.

## Rollback

Si hubiera que revertir antes del PR 3:

```sql
DROP TABLE IF EXISTS diabetic_profiles;
```

No afecta a `users` ni a `meals`: la FK es de `diabetic_profiles` hacia
`users`, con `cascade="all, delete-orphan"` en el lado del modelo, así que
borrar la tabla no rompe nada.
