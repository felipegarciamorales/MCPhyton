# intercambio-monedas-mcp

Servidor MCP (construido con [fastmcp](https://github.com/jlowin/fastmcp)) que expone
una única tool, `get_exchange_rate`, que consume la API de tasas de cambio de
[frankfurter.dev](https://frankfurter.dev).

Este es un proyecto independiente, separado del proyecto `auth-service` en este
workspace (tiene su propio `pyproject.toml`, `.venv` y `uv.lock`).

## Ejecutar

Se sirve sobre HTTP streamable (no stdio) en `http://127.0.0.1:8001/mcp` por defecto
(puerto `8001`, no `8000`, para no chocar con el proyecto `auth-service` que usa por
defecto el puerto `8000`). Se puede sobreescribir con las variables de entorno
`MCP_HOST`, `MCP_PORT`, `MCP_PATH`.

Si tu red hace inspección TLS (proxy corporativo con una CA autofirmada) y las
llamadas a frankfurter.dev fallan con `CERTIFICATE_VERIFY_FAILED`, tené en cuenta que
la validación del certificado TLS para esa llamada saliente está desactivada a propósito
en el código (`VERIFY_SSL = False` en `server.py`) para este proyecto de demostración.
**Esto expone la conexión a ataques de tipo man-in-the-middle — está bien para una demo
local, pero nunca lo hagas así en producción** (reactivalo poniendo `VERIFY_SSL = True`
antes de usarlo en un entorno real).

```powershell
uv run intercambio-monedas-mcp
```

o directamente:

```powershell
uv run python -m intercambio_monedas_mcp.server
```

## Autenticación

Toda solicitud a este servidor requiere el header `Authorization: Bearer <jwt>` con un
JWT emitido por el proyecto hermano `autenticacion` (comparten el mismo secreto HS256).
Se configura con `AUTH_JWT_SECRET_KEY` / `AUTH_JWT_ALGORITHM` (mismos nombres de
variable de entorno que usa `auth-service`, así ambos servicios pueden compartir un
solo valor). Sin ese header, el endpoint del MCP devuelve `401 Unauthorized` antes de
que la solicitud llegue a cualquier tool.

La tool `get_exchange_rate` además valida el claim `type` del token y rechaza los
refresh tokens — solo los access tokens emitidos por `/auth/login` o `/auth/refresh`
pueden usarla.

## Tool

- `get_exchange_rate(currency_from="USD", currency_to="EUR", currency_date="latest")`:
  devuelve los datos de la tasa de cambio desde `https://api.frankfurter.dev/v1/{currency_date}`.

