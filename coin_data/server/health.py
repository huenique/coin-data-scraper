from litestar import get


@get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
