# auth-service

Servicio de autenticación HTTP construido con **FastAPI** + **Python 3.12**, gestionado con **uv**, usando **JWT** para login, validación y refresco de tokens. Persistencia en **SQLite**. Arquitectura en capas al estilo **DDD** (Domain-Driven Design) aplicando **SOLID** y **Clean Code**.

## Arquitectura

```
src/auth_service/
├── domain/              # Entidades, value objects, puertos de repositorio, excepciones.
│   ├── entities/         (User, Token)
│   ├── value_objects/    (Email, PlainPassword)
│   ├── repositories/     (UserRepository, TokenRepository — interfaces/ABC)
│   └── exceptions.py
├── application/         # Casos de uso (orquestación), DTOs y puertos de infraestructura.
│   ├── dto.py
│   ├── ports/            (PasswordHasher, TokenProvider — interfaces/ABC)
│   └── use_cases/        (RegisterUser, LoginUser, RefreshToken, ValidateToken)
├── infrastructure/      # Implementaciones concretas de los puertos.
│   ├── persistence/      (SQLAlchemy + SQLite: models, repos)
│   └── security/         (bcrypt hasher, JWT provider)
├── presentation/        # Capa HTTP (FastAPI).
│   ├── api/               (router /auth)
│   ├── schemas/           (Pydantic request/response)
│   ├── dependencies.py    (inyección de dependencias)
│   └── error_handlers.py  (mapeo de excepciones de dominio a HTTP)
├── shared/clock.py      # Reloj centralizado (facilita pruebas con freezegun)
├── config.py            # Settings (pydantic-settings, variables de entorno AUTH_*)
└── main.py              # Composición de la app FastAPI
```

La regla de dependencia de DDD se respeta: `domain` no depende de nada; `application` solo depende de `domain`; `infrastructure` implementa los puertos definidos en `domain`/`application`; `presentation` solo conoce `application` (casos de uso) y usa inyección de dependencias de FastAPI para resolver las implementaciones concretas.

## Requisitos

- Python 3.12 (gestionado automáticamente por `uv`)
- [uv](https://docs.astral.sh/uv/)

## Instalación

```powershell
uv sync
```

## Ejecutar el servicio

```powershell
uv run uvicorn auth_service.main:app --reload
```

o bien, usando el script definido en `pyproject.toml`:

```powershell
uv run auth-service
```

La API queda disponible en `http://127.0.0.1:8000`, con documentación interactiva en `/docs`.

## Configuración (variables de entorno, prefijo `AUTH_`)

| Variable                          | Default                                   | Descripción                              |
|------------------------------------|--------------------------------------------|-------------------------------------------|
| `AUTH_DATABASE_URL`                 | `sqlite:///./auth_service.db`               | Cadena de conexión SQLAlchemy             |
| `AUTH_JWT_SECRET_KEY`                | *(placeholder, cambiar en producción)*     | Clave de firma HS256 — **obligatorio** cambiar en producción |
| `AUTH_JWT_ALGORITHM`                 | `HS256`                                    | Algoritmo JWT                             |
| `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`   | `60`                                        | Expiración del access token (1 hora)      |
| `AUTH_REFRESH_TOKEN_EXPIRE_MINUTES`  | `10080` (7 días)                           | Expiración del refresh token              |

Defínelas en un archivo `.env` en la raíz del proyecto (ignorado por git).

## Endpoints

| Método | Ruta              | Descripción                                               |
|--------|-------------------|-------------------------------------------------------------|
| POST   | `/auth/register`  | Crea un usuario (email + password).                        |
| POST   | `/auth/login`      | Valida credenciales y devuelve `access_token` + `refresh_token`. |
| POST   | `/auth/refresh`    | Rota el refresh token (el anterior queda revocado) y devuelve un nuevo par. |
| POST   | `/auth/validate`   | Valida un access token (firma, expiración, revocación). Siempre responde `200` con `{ "valid": bool, ... }`. |

### Políticas de seguridad aplicadas

- Contraseñas con **bcrypt** (vía passlib), nunca se almacenan en texto plano.
- Política de contraseña: 8–72 caracteres, al menos una letra y un dígito (72 es el límite técnico de bcrypt).
- Tokens firmados con JWT (HS256) y **también** registrados en la base de datos (tabla `tokens`) para poder revocarlos — la sola validez criptográfica no basta.
- **Rotación de refresh tokens**: al refrescar, el token usado se revoca inmediatamente (no reutilizable).
- Mensajes de error de login genéricos (no se revela si el email existe o la contraseña es incorrecta).
- Sin secretos hardcodeados en el código: la clave JWT se lee de variables de entorno.

## Pruebas

```powershell
uv run pytest
```

La suite cubre:
- **Unitarias de dominio**: value objects (`Email`, `PlainPassword`) y entidades (`Token`), incluyendo casos límite (longitud mínima/máxima de password, instante exacto de expiración).
- **Unitarias de aplicación**: los 4 casos de uso con *fakes* (dobles de prueba) para los puertos — sin tocar red ni base de datos real.
- **Unitarias de infraestructura**: `BcryptPasswordHasher`, `JwtTokenProvider` (con `freezegun` para controlar expiración) y los repositorios SQLite (con SQLite en memoria).
- **Integración**: flujo HTTP completo contra la app FastAPI real (`TestClient`), con SQLite en memoria inyectado vía `dependency_overrides`.

Incluye escenarios positivos, negativos y de frontera (límites de longitud de password, expiración exacta, reutilización de refresh tokens, tokens de otro tipo, etc.).
