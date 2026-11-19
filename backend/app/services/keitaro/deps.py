from collections.abc import Generator

from app.services.keitaro.client import KeitaroClient


def get_keitaro_client() -> Generator[KeitaroClient, None, None]:
    """FastAPI dependency: one client per request, always closed afterwards."""
    client = KeitaroClient()
    try:
        yield client
    finally:
        client.close()
