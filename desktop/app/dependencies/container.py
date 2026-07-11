"""Desktop service container."""

from desktop.app.services.api_client import APIClient
from desktop.app.services.config_service import ConfigService
from desktop.app.services.vote_service import VoteService


class DesktopContainer:
    """Dependency container for the desktop voting application."""

    def __init__(self, website_url: str) -> None:
        self.api_client = APIClient(base_url=website_url)
        self.config_service = ConfigService()
        self.vote_service = VoteService()


def get_desktop_container(website_url: str) -> DesktopContainer:
    return DesktopContainer(website_url=website_url)
