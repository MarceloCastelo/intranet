from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo('America/Recife')


def to_local(value: datetime | None) -> datetime | None:
    """Converte um datetime armazenado em UTC (datetime.utcnow()) para o
    horário local da empresa, para exibição nos templates."""
    if value is None:
        return value
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(LOCAL_TZ)
