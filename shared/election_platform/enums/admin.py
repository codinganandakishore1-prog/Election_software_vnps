"""Administrative and reporting enumerations."""

from enum import Enum


class LoginStatus(str, Enum):
    """User login attempt outcomes."""

    SUCCESS = "Success"
    FAILED = "Failed"
    LOCKED = "Locked"


class NotificationType(str, Enum):
    """System notification categories."""

    NODE_OFFLINE = "Node Offline"
    NODE_ONLINE = "Node Online"
    ELECTION_PUBLISHED = "Election Published"
    ELECTION_STARTED = "Election Started"
    ELECTION_PAUSED = "Election Paused"
    ELECTION_RESUMED = "Election Resumed"
    ELECTION_ENDED = "Election Ended"
    BACKUP_COMPLETED = "Backup Completed"
    SYNC_FAILED = "Synchronization Failed"
    SYNC_COMPLETED = "Synchronization Completed"
    REPORT_DOWNLOADED = "Report Downloaded"
    ADMIN_ACTION = "Administrator Action"
    DATABASE_ERROR = "Database Error"


class BackupType(str, Enum):
    """Backup scope types."""

    DATABASE = "Database"
    CONFIGURATION = "Configuration"
    SYSTEM = "System"


class BackupStatus(str, Enum):
    """Backup job statuses."""

    COMPLETED = "Completed"
    RUNNING = "Running"
    FAILED = "Failed"


class ReportType(str, Enum):
    """Generated report formats."""

    EXCEL = "Excel"
    CSV = "CSV"
    PDF = "PDF"


class InstallStatus(str, Enum):
    """Configuration install outcomes on voting nodes."""

    DOWNLOADED = "Downloaded"
    INSTALLED = "Installed"
    FAILED = "Failed"


class SessionStatus(str, Enum):
    """Authenticated node session states."""

    ACTIVE = "Active"
    EXPIRED = "Expired"
    LOGGED_OUT = "Logged Out"


class SyncLogStatus(str, Enum):
    """Synchronization batch outcomes."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


class LocalVoteSyncStatus(str, Enum):
    """Desktop local vote synchronization states."""

    PENDING = "Pending"
    UPLOADING = "Uploading"
    ACKNOWLEDGED = "Acknowledged"
    RETRYING = "Retrying"
    COMPLETED = "Completed"
    FAILED = "Failed"
