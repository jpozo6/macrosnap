# 2026-04-24 — Columnas de reset de contraseña en `users`

Añade dos columnas nullable en la tabla `users` para soportar el flujo de
restablecimiento de contraseña por email:

- `reset_password_token` — `VARCHAR(255)` nullable, único, indexado
- `reset_password_token_expires_at` — `DATETIME` nullable

## Impacto en producción

Ambas columnas son nullable y sin default complejo, por lo que no requieren
backfill. `Base.metadata.create_all(bind=engine)` al arrancar la app crea las
columnas en bases de datos nuevas; para bases existentes, ejecutar manualmente:

```sql
ALTER TABLE users ADD COLUMN reset_password_token VARCHAR(255);
ALTER TABLE users ADD COLUMN reset_password_token_expires_at DATETIME;
CREATE UNIQUE INDEX ix_users_reset_password_token
    ON users (reset_password_token);
```

No hay pérdida de datos ni breaking changes: los usuarios existentes mantienen
su contraseña, y las columnas nuevas quedan a `NULL` hasta que alguien use el
flujo de forgot-password.
