from intercambio_monedas_mcp.server import HOST, PATH, PORT, mcp


def main() -> None:
    mcp.run(transport="http", host=HOST, port=PORT, path=PATH)
