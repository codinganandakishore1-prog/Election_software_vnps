"""Mock data for the administration shell (no backend connection)."""

from dataclasses import dataclass

from election_platform import __version__

APP_VERSION = __version__
SCHOOL_NAME = "Vidhya Niketan Public School"
SCHOOL_LOGO_URL = "/branding/school_logo.png"
ELECTION_NAME = "School Election 2026"

MOCK_USERS: dict[str, dict[str, str]] = {
    "admin": {
        "password": "admin123",
        "role": "Administrator",
        "display_name": "Election Administrator",
    },
    "superadmin": {
        "password": "super123",
        "role": "Super Administrator",
        "display_name": "Super Administrator",
    },
    "viewer": {
        "password": "viewer123",
        "role": "Viewer",
        "display_name": "Results Viewer",
    },
}


@dataclass(frozen=True)
class NavItem:
    """Sidebar navigation entry."""

    label: str
    icon: str
    route: str
    section: str = "main"


NAV_ITEMS: list[NavItem] = [
    NavItem("Dashboard", "dashboard", "/dashboard"),
    NavItem("Live Results", "live_tv", "/live-results"),
    NavItem("Regular Election", "how_to_vote", "/regular-election"),
    NavItem("House Election", "home", "/house-election"),
    NavItem("Candidates", "groups", "/candidates"),
    NavItem("Positions", "badge", "/positions"),
    NavItem("Election Management", "event", "/elections"),
    NavItem("Node Monitor", "devices", "/nodes"),
    NavItem("Reports", "description", "/reports"),
    NavItem("Analytics", "bar_chart", "/analytics"),
    NavItem("Audit Logs", "history", "/audit-logs"),
    NavItem("Theme & Branding", "palette", "/theme-branding"),
    NavItem("Settings", "settings", "/settings"),
    NavItem("Documentation", "help", "/help"),
    NavItem("Profile", "person", "/profile"),
]

DASHBOARD_STATS: list[dict[str, str]] = [
    {"label": "Election", "value": ELECTION_NAME, "icon": "event", "color": "primary"},
    {"label": "Status", "value": "LIVE", "icon": "fiber_manual_record", "color": "positive", "badge": True},
    {"label": "Votes Cast", "value": "1,864", "icon": "how_to_vote", "color": "primary"},
    {"label": "Nodes Online", "value": "16 / 16", "icon": "devices", "color": "positive"},
    {"label": "Pending Queue", "value": "3", "icon": "pending_actions", "color": "warning"},
    {"label": "Last Vote", "value": "2 sec ago", "icon": "schedule", "color": "info"},
    {"label": "Sync Errors", "value": "0", "icon": "sync_problem", "color": "positive"},
    {"label": "Connected Users", "value": "4", "icon": "people", "color": "primary"},
]

SYSTEM_STATUS: list[dict[str, str]] = [
    {"label": "Website", "value": "Online", "status": "ok"},
    {"label": "Database", "value": "Connected", "status": "ok"},
    {"label": "WebSocket", "value": "Standby", "status": "neutral"},
]

RECENT_ACTIVITY: list[dict[str, str]] = [
    {"time": "09:21", "message": "Node 05 connected"},
    {"time": "09:24", "message": "Vote received from Regular-03"},
    {"time": "09:25", "message": "Candidate configuration updated"},
    {"time": "09:30", "message": "Report downloaded by admin"},
    {"time": "09:32", "message": "Node 12 heartbeat received"},
]

NODE_HEALTH: list[dict[str, str]] = [
    {"name": "Regular-01", "status": "Online", "votes": "248", "queue": "0"},
    {"name": "Regular-02", "status": "Online", "votes": "252", "queue": "1"},
    {"name": "House-01", "status": "Online", "votes": "72", "queue": "0"},
    {"name": "House-02", "status": "Online", "votes": "68", "queue": "0"},
    {"name": "Regular-05", "status": "Online", "votes": "241", "queue": "2"},
    {"name": "House-03", "status": "Offline", "votes": "—", "queue": "—"},
]

NOTIFICATIONS: list[dict[str, str]] = [
    {"title": "Election is live", "time": "5 min ago", "icon": "campaign"},
    {"title": "All nodes online", "time": "12 min ago", "icon": "devices"},
    {"title": "3 votes pending sync", "time": "18 min ago", "icon": "sync"},
]

PLACEHOLDER_PAGES: dict[str, dict[str, str]] = {}
