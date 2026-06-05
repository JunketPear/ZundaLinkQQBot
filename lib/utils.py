from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple


def mask_key(value: str) -> str:
    if len(value) < 10:
        return "***"
    return f"{value[:4]}********{value[-4:]}"


def _format_time(value: str, fmt: str = "%H:%M") -> str:
    if not value:
        return ""
    try:
        return (
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            .astimezone(timezone(timedelta(hours=8)))
            .strftime(fmt)
        )
    except ValueError:
        return ""

def build_status_sections(conf: Dict[str, Any], data: Dict[str, Any]) -> Tuple[str, List[str], List[str]]:
    if not data:
        return "", [], []
    upd = _format_time(data.get("generatedAt", ""), "%H:%M:%S")
    online_players = data.get("currentOnlinePlayers", [])
    online_lines = [
        f"• [{_format_time(p['loginTime'])}] {p['userName']}" for p in online_players
    ]
    playing_names = {p.get("userName") for p in online_players}
    records = data.get("recentSessionRecords", [])
    recent_lines: List[str] = []
    seen = set()
    for record in records:
        name = record.get("userName", "未知")
        if name in seen or name in playing_names:
            continue
        seen.add(name)
        login_time = _format_time(record.get("loginTime", ""))
        recent_lines.append(f"• [{login_time}] {name} ({record.get('duration', 0) // 60}min)")
    return upd, online_lines, recent_lines
