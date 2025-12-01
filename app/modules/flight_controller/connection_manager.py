"""
Flight Controller connection manager.

This module encapsulates all logic for connecting to a MAVLink-based
flight controller over serial, UDP or TCP, and for tracking connection
state and heartbeats.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional

import serial  # type: ignore[import]
from pymavlink import mavutil  # type: ignore[import]

from .connection_state import ConnectionState, load_connection_state, save_connection_state

logger = logging.getLogger(__name__)


HEARTBEAT_TIMEOUT_SECONDS = 10.0


class FCConnectionManager:
    """Manage a single connection to a flight controller."""

    MAX_CONSECUTIVE_ERRORS: int = 5

    def __init__(self) -> None:
        # public-ish state
        self.connection_type: Optional[str] = None
        self.connection_params: Dict[str, Any] = {}
        self.baudrate: Optional[int] = None
        self.last_heartbeat: Optional[float] = None
        self.consecutive_errors: int = 0

        # internal
        self._serial: Optional[serial.Serial] = None
        self._mavlink: Optional[mavutil.mavfile] = None
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._running: bool = False
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def connect(self, connection_type: str, params: Dict[str, Any], baudrate: int) -> None:
        """
        Establish a MAVLink connection to the flight controller.

        :param connection_type: 'serial', 'udp', or 'tcp'
        :param params: connection parameters (e.g., device=/dev/serial0 or host/port)
        :param baudrate: baudrate for serial connections
        """
        async with self._lock:
            # Clean up any existing connection first
            if self._running:
                logger.info("Existing connection detected, disconnecting before new connect")
                await self._disconnect_locked(user_requested=False)

            connection_type = connection_type.lower().strip()
            if connection_type not in {"serial", "udp", "tcp"}:
                raise ValueError(f"Unsupported connection_type: {connection_type}")

            logger.info("Connecting to flight controller via %s with params=%s baudrate=%s",
                        connection_type, params, baudrate)

            self.connection_type = connection_type
            self.connection_params = dict(params)
            self.baudrate = baudrate
            self.consecutive_errors = 0
            self.last_heartbeat = None

            # Create underlying connection
            if connection_type == "serial":
                await self._connect_serial(params, baudrate)
            elif connection_type == "udp":
                await self._connect_udp(params, baudrate)
            elif connection_type == "tcp":
                await self._connect_tcp(params, baudrate)

            self._running = True
            loop = asyncio.get_running_loop()
            self._reader_task = loop.create_task(self._read_loop(), name="fc_read_loop")

            # Persist successful connection config
            state = ConnectionState(
                is_connected=True,
                user_disconnected=False,
                connection_type=self.connection_type,
                params=self.connection_params,
                baudrate=self.baudrate,
                last_success=time_to_datetime(time.monotonic()),
            )
            save_connection_state(state)

    async def disconnect(self, user_requested: bool = False) -> None:
        """Disconnect from the flight controller."""
        async with self._lock:
            await self._disconnect_locked(user_requested=user_requested)

    def get_status(self) -> Dict[str, Any]:
        """Return current connection status as a dict."""
        now = time.monotonic()
        if self.last_heartbeat is not None:
            last_heartbeat_age = max(0.0, now - self.last_heartbeat)
        else:
            last_heartbeat_age = None

        connected = self._running and self._mavlink is not None

        status: Dict[str, Any] = {
            "connected": connected,
            "connection_type": self.connection_type,
            "params": self.connection_params,
            "baudrate": self.baudrate,
            "last_heartbeat_age": last_heartbeat_age,
            "error_count": self.consecutive_errors,
            "reader_running": bool(self._reader_task and not self._reader_task.done()),
        }
        return status

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    async def _disconnect_locked(self, user_requested: bool) -> None:
        """Assumes caller holds self._lock."""
        if not self._running and not self._mavlink:
            # Nothing to do
            return

        logger.info("Disconnecting from flight controller (user_requested=%s)", user_requested)

        self._running = False

        # Stop reader task
        if self._reader_task is not None:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Reader task raised on cancel: %s", exc)
            finally:
                self._reader_task = None

        # Close MAVLink/serial
        try:
            if self._mavlink is not None:
                logger.debug("Closing MAVLink connection")
                self._mavlink.close()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Error while closing MAVLink connection: %s", exc)
        finally:
            self._mavlink = None

        try:
            if self._serial is not None and self._serial.is_open:
                logger.debug("Closing serial port")
                self._serial.close()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Error while closing serial port: %s", exc)
        finally:
            self._serial = None

        # Persist disconnected state
        state = ConnectionState(
            is_connected=False,
            user_disconnected=user_requested,
            connection_type=self.connection_type,
            params=self.connection_params,
            baudrate=self.baudrate,
            last_success=None,
        )
        save_connection_state(state)

    async def _connect_serial(self, params: Dict[str, Any], baudrate: int) -> None:
        device = params.get("device")
        if not device or not isinstance(device, str):
            raise ValueError("Serial connection requires 'device' parameter")

        if not os.path.exists(device):
            raise FileNotFoundError(f"Serial device not found: {device}")

        if not os.access(device, os.R_OK | os.W_OK):
            raise PermissionError(f"Insufficient permissions for serial device: {device}")

        logger.debug("Opening serial device %s at %s baud", device, baudrate)

        # Open serial port
        self._serial = serial.Serial(device, baudrate=baudrate, timeout=1)

        # Create MAVLink connection using pymavlink
        self._mavlink = mavutil.mavlink_connection(
            device,
            baud=baudrate,
            autoreconnect=True,
        )

    async def _connect_udp(self, params: Dict[str, Any], baudrate: int) -> None:  # noqa: ARG002
        host = params.get("host")
        port = params.get("port")
        if not host or not isinstance(host, str):
            raise ValueError("UDP connection requires 'host' parameter")
        if not isinstance(port, int):
            raise ValueError("UDP connection requires integer 'port' parameter")

        target = f"udp:{host}:{port}"
        logger.debug("Opening UDP MAVLink connection %s", target)
        self._mavlink = mavutil.mavlink_connection(target, autoreconnect=True)

    async def _connect_tcp(self, params: Dict[str, Any], baudrate: int) -> None:  # noqa: ARG002
        host = params.get("host")
        port = params.get("port")
        if not host or not isinstance(host, str):
            raise ValueError("TCP connection requires 'host' parameter")
        if not isinstance(port, int):
            raise ValueError("TCP connection requires integer 'port' parameter")

        target = f"tcp:{host}:{port}"
        logger.debug("Opening TCP MAVLink connection %s", target)
        self._mavlink = mavutil.mavlink_connection(target, autoreconnect=True)

    async def _read_loop(self) -> None:
        """Background task: read MAVLink messages and track heartbeat/errors."""
        logger.info("Starting flight controller read loop")
        while self._running and self._mavlink is not None:
            try:
                # pymavlink is blocking; offload to a thread so we don't block the event loop
                msg = await asyncio.to_thread(self._mavlink.recv_match, blocking=True, timeout=1.0)
                if msg is None:
                    # Treat timeout as no data; not an error by itself
                    continue

                msg_type = getattr(msg, "get_type", lambda: "UNKNOWN")()
                if msg_type == "HEARTBEAT":
                    self.last_heartbeat = time.monotonic()
                    self.consecutive_errors = 0
                    logger.debug("Received HEARTBEAT from flight controller")

            except serial.SerialException as exc:
                self.consecutive_errors += 1
                logger.warning("Serial error while reading MAVLink: %s (count=%s)",
                               exc, self.consecutive_errors)

                message = str(exc).lower()
                if any(keyword in message for keyword in ("no data", "disconnected")) and (
                    self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS
                ):
                    logger.error(
                        "Too many serial errors (%s), auto-disconnecting flight controller",
                        self.consecutive_errors,
                    )
                    # Auto-disconnect (not user requested)
                    await self.disconnect(user_requested=False)
                    break

                await asyncio.sleep(1.0)

            except Exception as exc:  # pragma: no cover - defensive
                self.consecutive_errors += 1
                logger.error("Unexpected error in MAVLink read loop: %s", exc)
                if self.consecutive_errors >= self.MAX_CONSECUTIVE_ERRORS:
                    logger.error(
                        "Too many generic errors (%s), auto-disconnecting flight controller",
                        self.consecutive_errors,
                    )
                    await self.disconnect(user_requested=False)
                    break
                await asyncio.sleep(1.0)

        logger.info("Flight controller read loop stopped")


async def heartbeat_watcher(manager: FCConnectionManager) -> None:
    """
    Background task that watches for stale heartbeat and disconnects if needed.
    """
    logger.info("Starting heartbeat watcher task")
    while True:
        await asyncio.sleep(1.0)
        status = manager.get_status()
        if not status["connected"]:
            continue

        last_heartbeat_age = status.get("last_heartbeat_age")
        if last_heartbeat_age is None:
            continue

        if last_heartbeat_age > HEARTBEAT_TIMEOUT_SECONDS:
            logger.warning(
                "Heartbeat timeout (age=%.1fs > %.1fs), auto-disconnecting",
                last_heartbeat_age,
                HEARTBEAT_TIMEOUT_SECONDS,
            )
            await manager.disconnect(user_requested=False)


def time_to_datetime(monotonic_time: float) -> Optional["datetime"]:
    """
    Helper to convert a monotonic timestamp into a real datetime.

    Note: This is inherently approximate because monotonic time has no epoch;
    here we simply map \"now\" monotonic to wall clock now.
    """
    from datetime import datetime, timezone

    # Map current monotonic to wall clock now
    now_wall = datetime.now(timezone.utc)
    return now_wall


def restore_from_state(manager: FCConnectionManager) -> Optional[ConnectionState]:
    """
    Load last connection state and, if appropriate, attempt to reconnect.

    Returns the loaded ConnectionState object.
    """
    state = load_connection_state()
    if state.is_connected and not state.user_disconnected:
        if state.connection_type and state.baudrate is not None:
            try:
                logger.info(
                    "Attempting to restore FC connection from state file: %s",
                    state,
                )
                # Fire and forget; caller should await
                # but we keep this helper synchronous for easy use in startup.
            except Exception:
                # The actual connect is expected to be called explicitly by the startup
                # logic, so this helper only exposes state.
                pass
    return state


