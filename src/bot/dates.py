"""Date helpers. The bot speaks DD.MM.YYYY to users everywhere; Linear stores
and expects ISO (YYYY-MM-DD), so we convert at the edges."""
from __future__ import annotations

from datetime import datetime


def parse_date(text: str) -> str | None:
    """Parse user input (DD.MM.YYYY or DD.MM.YY) into an ISO date string, or None."""
    text = (text or "").strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def fmt_date(iso: str | None) -> str:
    """Format an ISO date (from Linear) as DD.MM.YYYY for display; '—' if empty."""
    if not iso:
        return "—"
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d.%m.%Y")
    except ValueError:
        return iso
