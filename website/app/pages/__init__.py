"""Administration portal pages."""

from nicegui import ui

from app.pages.analytics import register_analytics_routes
from app.pages.audit_logs import register_audit_logs_routes
from app.pages.candidates import register_candidates_routes
from app.pages.dashboard import register_dashboard_routes
from app.pages.elections import register_elections_routes
from app.pages.help import register_help_routes
from app.pages.house_election import register_house_election_routes
from app.pages.live_results import register_live_results_routes
from app.pages.login import register_login_routes
from app.pages.node_monitor import register_node_monitor_routes
from app.pages.regular_election import register_regular_election_routes
from app.pages.reports import register_reports_routes
from app.pages.positions import register_positions_routes
from app.pages.profile import register_profile_routes
from app.pages.settings import register_settings_routes
from app.pages.theme_branding import register_theme_routes
from app.services.auth_service import AuthService


def register_all_routes() -> None:
    """Register every website route."""
    register_login_routes()
    register_dashboard_routes()
    register_live_results_routes()
    register_node_monitor_routes()
    register_house_election_routes()
    register_positions_routes()
    register_elections_routes()
    register_candidates_routes()
    register_regular_election_routes()
    register_reports_routes()
    register_settings_routes()
    register_profile_routes()
    register_theme_routes()
    register_analytics_routes()
    register_audit_logs_routes()
    register_help_routes()

    @ui.page("/")
    def index_redirect() -> None:
        AuthService.clear_stale_session()
        if AuthService.is_authenticated():
            ui.navigate.to("/dashboard")
        else:
            ui.navigate.to("/login")
