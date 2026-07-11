"""Website service container."""

from website.app.services.api_client import APIClient


class WebsiteContainer:
    """Dependency container for the NiceGUI website."""

    def __init__(self, backend_url: str) -> None:
        self.api_client = APIClient(base_url=backend_url)


def get_website_container(backend_url: str) -> WebsiteContainer:
    return WebsiteContainer(backend_url=backend_url)
