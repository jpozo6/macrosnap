# Migraciones

Actualmente el proyecto inicializa el schema con
`Base.metadata.create_all(bind=engine)` al arrancar la app
(ver `backend/app/main.py`). No usamos Alembic todavía.

## Cambios estructurales

Cuando se añaden o modifican tablas y queremos preservar datos
existentes en producción, hay dos caminos:

1. Backfill manual (lo que hicimos al introducir auth):
   - Parar contenedores en el server
   - Borrar el volumen `macrosnap_pgdata`
   - Levantar de nuevo y dejar que `create_all` cree el schema limpio
2. Configurar Alembic (recomendado a medio plazo):
   ```bash
   cd backend
   alembic init migrations
   # Configurar env.py para leer settings.database_url y target_metadata = Base.metadata
   alembic revision --autogenerate -m "baseline"
   alembic upgrade head
   ```

## Por qué este README existe

El validador `.claude/hooks/validators/check_migrations.py` exige que
exista este directorio cuando se hacen cambios estructurales en
`models.py`. Sirve como recordatorio de que necesitamos un plan
explícito de migraciones cuando crezca la base de usuarios.
