# PythonMCP

Este workspace contiene **dos proyectos Python independientes** (cada uno con su
propio `pyproject.toml`, `.venv` y `uv.lock`, sin compartir entorno virtual):

- [`autenticacion/`](autenticacion/) — servicio de autenticación JWT (`auth-service`),
  construido con FastAPI. Corre en el puerto **8000**.
- [`frankfurter-mcp/`](frankfurter-mcp/) — servidor MCP (`intercambio-monedas-mcp`),
  construido con `fastmcp`, que expone la tool `get_exchange_rate` consumiendo la API
  de [frankfurter.dev](https://frankfurter.dev). Corre en el puerto **8001** y requiere
  un JWT válido emitido por `auth-service` para poder usarse.

Guía para instalar herramientas, levantar ambos servicios, generar un token y
consumir el MCP. Incluye comandos para **Windows + PowerShell** y, como segunda
opción, para **macOS + bash/zsh**.

## Requisitos previos

- Python 3.12+ instalado.

  - Windows: ej. `C:\Program Files\Python314\python.exe`.
  - macOS: `python3 --version` (si no lo tenés, `brew install python@3.12`).

- [`uv`](https://docs.astral.sh/uv/) instalado. Si `uv` no está en el PATH, comprobalo con:

  **Windows (PowerShell):**
  ```powershell
  Get-Command uv -ErrorAction SilentlyContinue
  ```

  **macOS (bash/zsh):**
  ```bash
  command -v uv
  ```

  Si no aparece nada en Windows, usalo a través del módulo de Python:

  ```powershell
  & "C:/Program Files/Python314/python.exe" -m uv --version
  ```

  O instalá el ejecutable standalone de `uv` (recomendado en ambos sistemas, para
  poder escribir simplemente `uv` en vez de la ruta completa):

  **Windows (PowerShell):**
  ```powershell
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

  **macOS (bash/zsh):**
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  (o `brew install uv` si usás Homebrew)

  Después de instalarlo, cerrá y volvé a abrir la terminal para que tome el PATH
  actualizado.

- Si estás en una red corporativa que intercepta TLS (certificados autofirmados),
  puede que necesites pasar `--native-tls` (deprecado) o `--system-certs` a los
  comandos `uv add` / `uv sync` para que puedan descargar paquetes de PyPI (aplica
  igual en Windows y macOS).

## 1. Instalar dependencias de cada proyecto

Cada proyecto se instala por separado, parándose dentro de su carpeta.

**Windows (PowerShell):**
```powershell
cd C:\PC\PythonMCP\autenticacion
uv sync

cd C:\PC\PythonMCP\frankfurter-mcp
uv sync
```

**macOS (bash/zsh):**
```bash
cd ~/PythonMCP/autenticacion
uv sync

cd ~/PythonMCP/frankfurter-mcp
uv sync
```

## 2. Levantar los servicios (orden importa)

Primero **siempre** `auth-service`, porque el MCP valida los JWT que este emite.
Usá dos terminales distintas (o dos pestañas) para dejarlos corriendo en paralelo.

**Terminal 1 — auth-service (puerto 8000):**

Windows (PowerShell):
```powershell
cd C:\PC\PythonMCP\autenticacion
uv run uvicorn auth_service.main:app --port 8000
```
macOS (bash/zsh):
```bash
cd ~/PythonMCP/autenticacion
uv run uvicorn auth_service.main:app --port 8000
```

**Terminal 2 — MCP de intercambio de monedas (puerto 8001):**

Windows (PowerShell):
```powershell
cd C:\PC\PythonMCP\frankfurter-mcp
uv run intercambio-monedas-mcp
```
macOS (bash/zsh):
```bash
cd ~/PythonMCP/frankfurter-mcp
uv run intercambio-monedas-mcp
```

Al arrancar el MCP vas a ver este warning — es esperado, la validación TLS saliente
está desactivada a propósito para esta demo (ver [`frankfurter-mcp/README.md`](frankfurter-mcp/README.md)):
```
WARNING: HTTP_VERIFY_SSL=false — TLS certificate validation is DISABLED...
```

Para confirmar que ambos puertos están escuchando sin chocar entre sí:

Windows (PowerShell):
```powershell
Get-NetTCPConnection -LocalPort 8000,8001 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess
```
macOS (bash/zsh):
```bash
lsof -nP -iTCP:8000,8001 -sTCP:LISTEN
```

## 3. Generar un token (JWT)

**Terminal 3** (nueva terminal, para no interrumpir los servicios corriendo):

**Registrar un usuario** (si ya existe devuelve `409 Conflict`, no pasa nada, seguí
con el login):

Windows (PowerShell):
```powershell
$body = '{"email":"test@example.com","password":"SuperSecret123!","actor_type":"human"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/auth/register -Method Post -ContentType "application/json" -Body $body
```
macOS (bash/zsh):
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SuperSecret123!","actor_type":"human"}'
```

**Login para obtener el `access_token`:**

Windows (PowerShell):
```powershell
$loginBody = '{"email":"test@example.com","password":"SuperSecret123!"}'
$resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/auth/login -Method Post -ContentType "application/json" -Body $loginBody
$access = $resp.access_token
$access
```
macOS (bash/zsh):
```bash
RESP=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SuperSecret123!"}')

ACCESS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "$ACCESS"
```

Notas importantes:
- El `access_token` expira a los **60 minutos**. Pasado ese tiempo, repetí el login
  (o usá `POST /auth/refresh` con el `refresh_token` para renovarlo).
- Usá siempre el **`access_token`**, nunca el `refresh_token` — el MCP rechaza
  explícitamente los refresh tokens al llamar la tool, aunque su firma sea válida.

## 4. Consumir el MCP

### Opción A — Desde VS Code / Copilot Chat (modo agente)

Ya existe una configuración lista en [`.vscode/mcp.json`](.vscode/mcp.json). Pasos:

1. Abrí la paleta de comandos (`Ctrl+Shift+P`) → **MCP: List Servers**.
2. Seleccioná `intercambio-monedas` → **Start**.
3. Cuando te pida el `auth_token`, pegá el valor de `$access` del paso 3.
4. Listo — ahora el agente puede invocar `get_exchange_rate` directamente en el chat.

Si el token expira, volvé a correr el login y reiniciá el servidor MCP desde la
paleta de comandos para que te vuelva a pedir el token.

### Opción B — Con curl / Insomnia / Postman (protocolo MCP crudo)

El transporte streamable-http requiere primero un `initialize` para obtener un
`Mcp-Session-Id`, que luego hay que reenviar en la llamada a la tool:

Windows (PowerShell):
```powershell
$headers = @{
    "Content-Type"  = "application/json"
    "Accept"        = "application/json, text/event-stream"
    "Authorization" = "Bearer $access"
}

$init = Invoke-WebRequest -Uri http://127.0.0.1:8001/mcp -Method Post -Headers $headers `
  -Body '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":0}' `
  -UseBasicParsing
$headers["Mcp-Session-Id"] = $init.Headers["Mcp-Session-Id"]

$r = Invoke-WebRequest -Uri http://127.0.0.1:8001/mcp -Method Post -Headers $headers `
  -Body '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_exchange_rate","arguments":{"currency_from":"USD","currency_to":"EUR"}},"id":1}' `
  -UseBasicParsing
$r.Content
```

macOS (bash/zsh):
```bash
curl -s -D headers.txt -o /dev/null -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $ACCESS" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"curl-test","version":"1.0"}},"id":0}'

SESSION=$(grep -i "mcp-session-id" headers.txt | cut -d' ' -f2 | tr -d '\r')

curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Mcp-Session-Id: $SESSION" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"get_exchange_rate","arguments":{"currency_from":"USD","currency_to":"EUR"}},"id":1}'
```

En Insomnia/Postman: armá dos requests `POST` a `http://127.0.0.1:8001/mcp` con esos
mismos headers y bodies — primero el de `initialize` (copiando el `Mcp-Session-Id`
que viene en la respuesta), y después el de `tools/call` usando ese session id.

**Sin el header `Authorization`, cualquier solicitud devuelve `401 Unauthorized`**
antes de llegar a la tool.

## Monedas soportadas

Frankfurter.dev usa las tasas de referencia del Banco Central Europeo, por lo que
**no incluye el peso colombiano (`COP`)**. Entre las monedas disponibles están:
`USD`, `EUR`, `GBP`, `JPY`, `CNY`, `MXN`, `BRL`, `CAD`, `CHF`, `INR`, etc. Lista
completa en `GET https://api.frankfurter.dev/v1/currencies`.

## Resolución de problemas comunes

| Problema | Causa / Solución |
|---|---|
| `401 Unauthorized` al llamar al MCP | Falta el header `Authorization: Bearer <access_token>`, o el token expiró/es inválido. |
| `{"error": "A valid JWT access token is required..."}` | Se envió un `refresh_token` en vez de un `access_token`. |
| `400 Bad Request: Missing session ID` | Falta llamar primero a `initialize` y reenviar el `Mcp-Session-Id` recibido. |
| `CERTIFICATE_VERIFY_FAILED` al llamar a frankfurter.dev | Red corporativa con interceptación TLS; ya está mitigado con `VERIFY_SSL = False` en `frankfurter-mcp/server.py`. |
| Puerto 8000 u 8001 ocupado | Otro proceso quedó corriendo de una prueba anterior. Windows: `Get-NetTCPConnection -LocalPort 8000,8001 -State Listen` y `Stop-Process -Id <PID> -Force`. macOS: `lsof -nP -iTCP:8000,8001 -sTCP:LISTEN` y `kill -9 <PID>`. |
| `uv: command not found` en una terminal nueva | Windows: usá `& "C:/Program Files/Python314/python.exe" -m uv <comando>` o instalá el binario standalone. macOS: asegurate de que `~/.local/bin` (o `/opt/homebrew/bin` si usaste brew) esté en tu `$PATH`, o reabrí la terminal tras instalar `uv`. |
