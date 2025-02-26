from dataclasses import dataclass

from litestar import get


@dataclass
class HealthCheckResponse:
    status: str


@get("/health")
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="ok")
