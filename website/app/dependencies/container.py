"""Website service container."""

from app.config.settings import settings
from app.services.api_client import APIClient

_container: "WebsiteContainer | None" = None


class WebsiteContainer:
    """Dependency container for the NiceGUI website."""

    def __init__(self, backend_url: str, api_prefix: str) -> None:
        self.api_client = APIClient(base_url=f"{backend_url.rstrip('/')}{api_prefix}")


def init_website_container(backend_url: str | None = None, api_prefix: str | None = None) -> WebsiteContainer:
    """Initialize the shared website container."""
    global _container
    _container = WebsiteContainer(
        backend_url=backend_url or settings.backend_url,
        api_prefix=api_prefix or settings.api_prefix,
    )
    return _container


def get_website_container() -> WebsiteContainer:
    """Return the shared website container, initializing if needed."""
    if _container is None:
        return init_website_container()
    return _container
