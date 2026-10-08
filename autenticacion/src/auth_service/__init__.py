def main() -> None:
    import uvicorn

    from auth_service.config import get_settings

    settings = get_settings()
    uvicorn.run("auth_service.main:app", host=settings.host, port=settings.port, reload=True)
