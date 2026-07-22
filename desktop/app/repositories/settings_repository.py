"""Desktop local settings repository."""

from sqlalchemy.orm import Session

from app.models.desktop_setting import LocalSetting
from app.repositories.base import LocalBaseRepository


class LocalSettingsRepository(LocalBaseRepository[LocalSetting]):
    """Data access for local key-value settings."""

    model = LocalSetting

    def get_value(self, setting_key: str) -> str | None:
        record = self.get_by_field("setting_key", setting_key)
        return record.setting_value if record else None

    def set_value(self, setting_key: str, setting_value: str) -> LocalSetting:
        record = self.get_by_field("setting_key", setting_key)
        if record is None:
            record = LocalSetting(setting_key=setting_key, setting_value=setting_value)
            self.add(record)
        else:
            record.setting_value = setting_value
        return record
