# Hidroequipos Backend

Backend en FastAPI para gestionar usuarios sobre Postgres/Supabase. La API usa JWT en cookie HTTP-only y expone un conjunto de rutas para autenticación y mantenimiento de usuarios.

## Requisitos

- Python 3.13 o superior.
- `uv` instalado.
- Una base de datos Postgres accesible localmente o en Supabase.
- Un frontend corriendo en el origen que configures en `FRONTEND_ORIGIN`.

## Instalación local

1. Clona el repositorio.
2. Copia `.env.example` a `.env`.
3. Ajusta las variables de entorno según tu entorno de desarrollo.
4. Instala dependencias con `uv sync`.
5. Levanta la aplicación con `uv run fastapi dev src/app/main.py`.

## Variables de entorno

La aplicación lee la configuración desde `.env`. Estas son las variables usadas por el backend:

- `ENVIRONMENT`: entorno de ejecución. En `development` la cookie de sesión no fuerza `Secure`.
- `FRONTEND_ORIGIN`: origen exacto permitido por CORS, por ejemplo `http://localhost:3000`.
- `DATABASE_URL`: cadena de conexión async a Postgres. Para Supabase usa SSL.
- `JWT_SECRET_KEY`: secreto largo y aleatorio para firmar tokens.
- `JWT_ALGORITHM`: algoritmo JWT, por defecto `HS256`.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: duración del token de acceso en minutos.
- `AUTH_COOKIE_NAME`: nombre de la cookie de autenticación, por defecto `access_token`.
- `AUTH_COOKIE_SECURE`: fuerza la cookie con `Secure` cuando se activa.
- `AUTH_COOKIE_SAMESITE`: valor de SameSite de la cookie, por defecto `lax`.

Ejemplo de `DATABASE_URL` para Supabase:

```env
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres?ssl=require
```

## Ejecutar en desarrollo

Con la configuración cargada en `.env`, el flujo habitual es:

```bash
uv sync
uv run fastapi dev src/app/main.py
```

Si prefieres ejecutar con Uvicorn, también puedes usar:

```bash
uv run uvicorn app.main:app --reload --app-dir src
```

## Estructura de la API

- `GET /health`: endpoint simple de verificación.
- `POST /api/v1/users/register`: crea usuario y deja la cookie de sesión.
- `POST /api/v1/users/login`: autentica y deja la cookie de sesión.
- `POST /api/v1/users/logout`: elimina la cookie HTTP-only.
- `GET /api/v1/users/me`: devuelve el usuario autenticado.
- `PATCH /api/v1/users/{user_uuid}`: actualiza un usuario.
- `DELETE /api/v1/users/{user_uuid}`: baja lógica del usuario.

La autenticación usa un JWT firmado en la cookie HTTP-only `access_token`. En desarrollo la cookie se crea sin `Secure`; fuera de desarrollo el backend fuerza `Secure`.

## Notas de desarrollo

- CORS solo acepta el origen configurado en `FRONTEND_ORIGIN` y permite credenciales.
- El modelo de usuarios trabaja sobre la tabla `public.usuarios`.
- El borrado es lógico: marca el usuario como inactivo y completa `deleted_at`.
- La contraseña debe tener al menos 8 caracteres y mezclar letras y números.

## Verificación rápida

Una vez levantado el servidor, prueba:

```bash
curl http://127.0.0.1:8000/health
```

La documentación interactiva de FastAPI queda disponible en `/docs`.
