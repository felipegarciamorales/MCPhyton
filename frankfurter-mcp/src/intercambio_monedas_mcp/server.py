"""MCP server exposing a currency exchange rate tool backed by frankfurter.dev."""

import logging
import os

import httpx as http
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.dependencies import get_access_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# default port 8001 (not 8000) to avoid colliding with the auth-service project
HOST = os.environ.get("MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("MCP_PORT", "8001"))
PATH = os.environ.get("MCP_PATH", "/mcp")

# same env var name as auth-service's pydantic settings (env_prefix "AUTH_" + jwt_secret_key)
# so both services can share one secret; override in production via env, don't hardcode.
JWT_SECRET_KEY = os.environ.get(
    "AUTH_JWT_SECRET_KEY", "change-this-secret-key-in-production-min-32-bytes"
)
JWT_ALGORITHM = os.environ.get("AUTH_JWT_ALGORITHM", "HS256")

# requires every MCP request to carry "Authorization: Bearer <jwt>" signed by auth-service
auth_provider = JWTVerifier(public_key=JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

mcp = FastMCP("Intercambio de Monedas", auth=auth_provider)

# opt-in only: disables TLS certificate validation for the outbound call to
# frankfurter.dev, exposing it to man-in-the-middle attacks. Use only to work
# around a trusted corporate proxy doing TLS interception, never in production.
VERIFY_SSL = False
if not VERIFY_SSL:
    logger.warning(
        "HTTP_VERIFY_SSL=false — TLS certificate validation is DISABLED for "
        "calls to frankfurter.dev. Do not use this in production."
    )


@mcp.tool
def get_exchange_rate(
    currency_from: str = "USD",
    currency_to: str = "EUR",
    currency_date: str = "latest",
):
    """Use this to get current exchange rate.

    Args:
        currency_from: The currency to convert from (e.g., "USD").
        currency_to: The currency to convert to (e.g., "EUR").
        currency_date: The date for the exchange rate or "latest". Defaults to "latest".

    Returns:
        A dictionary containing the exchange rate data, or an error message if the request fails.
    """
    access_token = get_access_token()
    # JWTVerifier already rejected missing/expired/tampered tokens at the transport
    # level; this also rejects refresh tokens, which auth-service issues but which
    # must not be usable to call protected APIs.
    if access_token is None or access_token.claims.get("type") != "access":
        logger.warning("Rejected get_exchange_rate call: missing or invalid JWT access token")
        return {"error": "A valid JWT access token is required to call this tool"}

    logger.info(
        f"--- 🔧 Tool: get_exchange_rate called for converting {currency_from} to {currency_to} ---"
    )
    try:
        response = http.get(
            f"https://api.frankfurter.dev/v1/{currency_date}",
            params={"from": currency_from, "to": currency_to},
            verify=VERIFY_SSL,
        )
        response.raise_for_status()

        data = response.json()
        if "rates" not in data:
            return {"error": "Invalid response from exchange rate API"}
        return data
    except http.HTTPError as e:
        logger.error(f"HTTP error fetching exchange rate: {e}")
        return {"error": f"HTTP error fetching exchange rate: {e}"}
    except ValueError as e:
        logger.error(f"JSON error fetching exchange rate: {e}")
        return {"error": f"JSON error fetching exchange rate: {e}"}


if __name__ == "__main__":
    mcp.run(transport="http", host=HOST, port=PORT, path=PATH)
