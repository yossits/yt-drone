"""
Connection state persistence for Flight Controller connection.

Stores the last known connection configuration and state in a JSON file so
the server can restore the connection on startup.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = DATA_DIR / "flight_controller_connection.json"


@dataclass
class ConnectionState:
    """Represents the persisted connection state for the flight controller."""

    is_connected: bool = False
    user_disconnected: bool = False
    connection_type: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    baudrate: Optional[int] = None
    last_success: Optional[datetime] = None

    def to_serializable_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Convert datetime to ISO string
        if self.last_success is not None:
            data["last_success"] = self.last_success.astimezone(timezone.utc).isoformat()
        else:
            data["last_success"] = None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectionState":
        last_success_raw = data.get("last_success")
        last_success_dt: Optional[datetime]
        if isinstance(last_success_raw, str):
            try:
                last_success_dt = datetime.fromisoformat(last_success_raw)
            except ValueError:
                logger.warning("Invalid last_success value in state file, ignoring")
                last_success_dt = None
        else:
            last_success_dt = None

        return cls(
            is_connected=bool(data.get("is_connected", False)),
            user_disconnected=bool(data.get("user_disconnected", False)),
            connection_type=data.get("connection_type"),
            params=dict(data.get("params", {})),
            baudrate=data.get("baudrate"),
            last_success=last_success_dt,
        )


def load_connection_state() -> ConnectionState:
    """Load connection state from the JSON file, or return defaults if missing/invalid."""
    if not STATE_FILE.exists():
        logger.info("Connection state file does not exist, using defaults")
        return ConnectionState()

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read connection state file %s: %s", STATE_FILE, exc)
        return ConnectionState()

    if not isinstance(raw, dict):
        logger.warning("Unexpected data in connection state file, resetting to defaults")
        return ConnectionState()

    state = ConnectionState.from_dict(raw)
    logger.debug("Loaded connection state: %s", state)
    return state


def save_connection_state(state: ConnectionState) -> None:
    """Persist the connection state to the JSON file."""
    try:
        serializable = state.to_serializable_dict()
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)
        logger.debug("Saved connection state to %s", STATE_FILE)
    except OSError as exc:
        logger.error("Failed to write connection state file %s: %s", STATE_FILE, exc)


