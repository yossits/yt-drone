"""
FCConnectionManager - Manages persistent MAVLink connection to Flight Controller
"""

import asyncio
import logging
import serial
import time
from typing import Dict, List, Optional, Any
from pymavlink import mavutil

from app.fc.decoders import decode_mavlink_message

logger = logging.getLogger(__name__)


class FCConnectionManager:
    """
    Manages a single persistent connection to the Flight Controller via MAVLink.
    Implements pub/sub pattern for distributing MAVLink messages to subscribers.
    """
    
    def __init__(self):
        """Initialize the connection manager"""
        self._connection: Optional[serial.Serial] = None
        self._mavlink: Optional[mavutil.mavlink_connection] = None
        self._read_task: Optional[asyncio.Task] = None
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
        self._device: Optional[str] = None
        self._baud: Optional[int] = None
        self._running = False
        self._last_heartbeat_time: Optional[float] = None
    
    async def connect(self, device: str, baud: int) -> bool:
        """
        Connect to Flight Controller via serial port
        Args:
            device: Serial device path (e.g., '/dev/ttyAMA0')
            baud: Baud rate (e.g., 57600)
        Returns:
            True if connection succeeded
        Raises:
            ValueError: If already connected
            serial.SerialException: If serial connection fails
            FileNotFoundError: If device doesn't exist
            PermissionError: If permission denied
            Exception: For other connection errors
        """
        async with self._lock:
            if self._connection is not None:
                logger.warning("Already connected. Disconnect first.")
                raise ValueError("Already connected. Disconnect first.")
            
            try:
                # Create MAVLink connection using device and baud as separate parameters
                # This is the correct format for pymavlink - not as a connection string
                logger.info(f"Connecting to {device} at {baud} baud")
                logger.info("Creating MAVLink connection object...")
                
                self._mavlink = mavutil.mavlink_connection(
                    device,
                    baud=baud,
                    source_system=255,
                    source_component=0
                )
                logger.info("MAVLink connection object created successfully")
                
                # Get the underlying serial connection from mavlink
                if hasattr(self._mavlink, 'port') and hasattr(self._mavlink.port, 'ser'):
                    self._connection = self._mavlink.port.ser
                    logger.info(f"Retrieved serial connection from MAVLink port (is_open: {self._connection.is_open})")
                else:
                    # Fallback: create our own serial connection for status checking
                    logger.warning("MAVLink port.ser not found, creating fallback serial connection")
                    logger.warning(f"Attempting to create serial connection to {device} at {baud} baud")
                    try:
                        self._connection = serial.Serial(
                            device,
                            baud,
                            timeout=1,
                            write_timeout=1
                        )
                        logger.info(f"Fallback serial connection created (port: {self._connection.port}, is_open: {self._connection.is_open})")
                    except Exception as e:
                        logger.error(f"Failed to create fallback serial connection: {e}", exc_info=True)
                        raise
                
                # Verify serial connection is actually open
                if self._connection is None:
                    logger.error("Serial connection is None after initialization")
                    raise Exception("Serial connection is None after initialization")
                
                is_open = self._connection.is_open if hasattr(self._connection, 'is_open') else False
                port_name = getattr(self._connection, 'port', 'unknown')
                
                logger.info(f"Checking serial connection: port={port_name}, is_open={is_open}, device={device}, baud={baud}")
                
                if not is_open:
                    logger.error(f"Serial connection is not open! Port: {port_name}")
                    raise Exception(f"Serial connection failed to open on {port_name}")
                
                logger.info(f"Serial connection verified: port={port_name}, is_open={is_open}, device={device}, baud={baud}")
                
                self._device = device
                self._baud = baud
                self._running = True
                logger.debug(f"Connection state initialized: device={self._device}, baud={self._baud}, running={self._running}")
                
                # Start read loop
                logger.info("Starting MAVLink read loop task...")
                try:
                    self._read_task = asyncio.create_task(self._read_loop())
                    logger.info("MAVLink read loop task started")
                except Exception as e:
                    logger.error(f"Failed to create read loop task: {e}", exc_info=True)
                    raise
                
                logger.info(f"Successfully connected to Flight Controller at {device} @ {baud} baud")
                return True
                
            except serial.SerialException as e:
                error_msg = f"Cannot access {device}: {str(e)}. Check permissions (user may need to be in 'dialout' group)."
                logger.error(error_msg)
                await self._cleanup()
                raise serial.SerialException(error_msg) from e
            except FileNotFoundError as e:
                error_msg = f"Device {device} does not exist"
                logger.error(error_msg)
                await self._cleanup()
                raise FileNotFoundError(error_msg) from e
            except PermissionError as e:
                error_msg = f"Permission denied accessing {device}. User may need to be in 'dialout' group."
                logger.error(error_msg)
                await self._cleanup()
                raise PermissionError(error_msg) from e
            except Exception as e:
                error_msg = f"Connection failed: {str(e)}"
                logger.error(f"Failed to connect to Flight Controller: {e}", exc_info=True)
                await self._cleanup()
                raise Exception(error_msg) from e
    
    async def disconnect(self) -> None:
        """
        Disconnect from Flight Controller
        """
        async with self._lock:
            if self._connection is None:
                logger.info("Already disconnected")
                return
            
            logger.info("Disconnecting from Flight Controller")
            self._running = False
            
            # Cancel read task
            if self._read_task is not None:
                self._read_task.cancel()
                try:
                    await self._read_task
                except asyncio.CancelledError:
                    pass
                self._read_task = None
            
            await self._cleanup()
            logger.info("Disconnected from Flight Controller")
    
    def is_connected(self) -> bool:
        """
        Check if connected to Flight Controller
        Returns:
            True if connected, False otherwise
        """
        if self._mavlink is None:
            return False
        # Check if mavlink connection is valid
        if hasattr(self._mavlink, 'port') and hasattr(self._mavlink.port, 'ser'):
            return self._mavlink.port.ser.is_open
        # Fallback: check our own connection
        return self._connection is not None and self._connection.is_open
    
    async def send_command(self, msg_builder) -> bool:
        """
        Send MAVLink command to Flight Controller
        Args:
            msg_builder: Function that builds and returns MAVLink message
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_connected() or self._mavlink is None:
            logger.warning("Cannot send command: not connected")
            return False
        
        try:
            msg = msg_builder(self._mavlink)
            self._mavlink.write(msg.pack(self._mavlink))
            logger.debug(f"Sent MAVLink command: {msg.get_type()}")
            return True
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    async def _read_loop(self) -> None:
        """
        Async read loop that receives MAVLink messages and distributes them via pub/sub
        """
        if self._connection is None or self._mavlink is None:
            logger.warning("Read loop: connection or mavlink is None, cannot start")
            return
        
        logger.info("Starting MAVLink read loop")
        message_count = 0
        first_message = True
        heartbeat_count = 0
        
        while self._running:
            try:
                # Read message from MAVLink (non-blocking)
                msg = self._mavlink.recv_match(blocking=False, timeout=0.1)
                
                if msg is not None:
                    message_count += 1
                    msg_type = msg.get_type()
                    
                    # Log first message received
                    if first_message:
                        logger.info(f"First MAVLink message received: {msg_type}")
                        first_message = False
                    
                    # Special logging for HEARTBEAT messages
                    if msg_type == "HEARTBEAT":
                        heartbeat_count += 1
                        current_time = time.time()
                        if self._last_heartbeat_time is not None:
                            time_since_last = current_time - self._last_heartbeat_time
                            logger.info(f"HEARTBEAT #{heartbeat_count} received (time since last: {time_since_last:.2f}s)")
                        else:
                            logger.info(f"HEARTBEAT #{heartbeat_count} received (first heartbeat)")
                        self._last_heartbeat_time = current_time
                    
                    # Categorize message
                    topic = self._categorize_message(msg)
                    
                    # Convert message to dict for JSON serialization
                    msg_dict = self._message_to_dict(msg)
                    # Preserve the message type name before it gets overridden
                    msg_dict["message_type"] = msg_type
                    
                    # Decode message to add human-readable fields
                    decoded_dict = decode_mavlink_message(msg_dict)
                    
                    # Log all message data to console (for debugging)
                    logger.debug(f"MAVLink message received - Type: {msg_type}, Type ID: {decoded_dict.get('type_id', 'N/A')}, Topic: {topic}, Data: {decoded_dict}")
                    
                    # Publish to subscribers
                    await self._publish(topic, decoded_dict)
                    
                    # Also publish to "raw" topic for all messages
                    if topic != "raw":
                        await self._publish("raw", decoded_dict)
                    
                    # Log every 100 messages to avoid spam
                    if message_count % 100 == 0:
                        logger.info(f"Processed {message_count} MAVLink messages (HEARTBEAT count: {heartbeat_count})")
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(0.01)
                
            except asyncio.CancelledError:
                logger.info(f"Read loop cancelled after processing {message_count} messages (HEARTBEAT count: {heartbeat_count})")
                break
            except Exception as e:
                logger.error(f"Error in read loop: {e}", exc_info=True)
                await asyncio.sleep(0.1)
        
        logger.info(f"MAVLink read loop stopped. Total messages processed: {message_count}, HEARTBEAT messages: {heartbeat_count}")
    
    def _categorize_message(self, msg) -> str:
        """
        Categorize MAVLink message into topic
        Args:
            msg: MAVLink message object
        Returns:
            Topic name: "status", "telemetry", "sensors", "map", or "raw"
        """
        msg_type = msg.get_type()
        
        # Status messages
        if msg_type in ["HEARTBEAT", "SYS_STATUS"]:
            return "status"
        
        # Telemetry messages
        if msg_type in ["ATTITUDE", "GLOBAL_POSITION_INT", "VFR_HUD", "BATTERY_STATUS"]:
            return "telemetry"
        
        # Sensor messages
        if msg_type in ["RAW_IMU", "SCALED_PRESSURE", "SCALED_IMU2", "RAW_PRESSURE"]:
            return "sensors"
        
        # Map/GPS messages
        if msg_type in ["GPS_RAW_INT", "GLOBAL_POSITION_INT"]:
            return "map"
        
        # All other messages go to raw
        return "raw"
    
    def _message_to_dict(self, msg) -> Dict[str, Any]:
        """
        Convert MAVLink message to dictionary for JSON serialization
        Args:
            msg: MAVLink message object
        Returns:
            Dictionary representation of the message
        """
        # Get message type (name) and ID
        msg_type = msg.get_type()
        msg_id = None
        
        # Try to get message ID using different methods
        try:
            if hasattr(msg, 'get_msgId'):
                msg_id = msg.get_msgId()
            elif hasattr(msg, '_id'):
                msg_id = msg._id
            elif hasattr(msg, 'id'):
                msg_id = msg.id
            elif hasattr(msg, 'MSG_ID'):
                msg_id = msg.MSG_ID
        except:
            msg_id = None
        
        # For HEARTBEAT messages, preserve the numeric 'type' field (MAV_TYPE)
        # before it gets overridden by the message type name
        mav_type_value = None
        if msg_type == "HEARTBEAT":
            if hasattr(msg, 'type'):
                mav_type_value = getattr(msg, 'type', None)
                logger.debug(f"HEARTBEAT detected, mav_type_value={mav_type_value}")
            else:
                logger.warning("HEARTBEAT message has no 'type' attribute")
        
        msg_dict = {
            "type": msg_type,  # Message type name (e.g., "HEARTBEAT")
            "type_id": msg_id,
            "timestamp": getattr(msg, "_timestamp", None),
        }
        
        # Preserve MAV_TYPE for HEARTBEAT if we captured it
        if mav_type_value is not None:
            msg_dict["mav_type"] = mav_type_value
        elif msg_type == "HEARTBEAT":
            logger.warning(f"HEARTBEAT but mav_type_value is None! msg fields: {msg.get_fieldnames() if hasattr(msg, 'get_fieldnames') else 'N/A'}")
        
        # Add all message fields
        # Note: For HEARTBEAT, the numeric 'type' field will override "type" above,
        # but we've already preserved it as "mav_type" for decoding
        for field in msg.get_fieldnames():
            value = getattr(msg, field, None)
            # Convert bytes to list for JSON serialization
            if isinstance(value, bytes):
                value = list(value)
            msg_dict[field] = value
        
        return msg_dict
    
    async def _publish(self, topic: str, message: Dict[str, Any]) -> None:
        """
        Publish message to all subscribers of a topic
        Args:
            topic: Topic name
            message: Message data (dict)
        """
        if topic not in self._subscribers:
            logger.debug(f"No subscribers for topic: {topic}")
            return
        
        # Copy list to avoid modification during iteration
        subscribers = self._subscribers[topic].copy()
        
        msg_type = message.get('type', 'unknown')
        logger.debug(f"Publishing message type {msg_type} to topic {topic} ({len(subscribers)} subscribers)")
        
        for queue in subscribers:
            try:
                # Non-blocking put
                queue.put_nowait(message)
                logger.debug(f"Message published to queue for topic {topic}")
            except asyncio.QueueFull:
                logger.warning(f"Queue full for topic {topic}, dropping message")
            except Exception as e:
                logger.error(f"Error publishing to queue: {e}")
    
    def subscribe(self, topic: str, queue: asyncio.Queue) -> None:
        """
        Subscribe a queue to a topic
        Args:
            topic: Topic name
            queue: asyncio.Queue instance to receive messages
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        if queue not in self._subscribers[topic]:
            self._subscribers[topic].append(queue)
            logger.debug(f"Subscribed queue to topic: {topic}")
    
    def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
        """
        Unsubscribe a queue from a topic
        Args:
            topic: Topic name
            queue: asyncio.Queue instance to remove
        """
        if topic in self._subscribers:
            if queue in self._subscribers[topic]:
                self._subscribers[topic].remove(queue)
                logger.debug(f"Unsubscribed queue from topic: {topic}")
            
            # Remove empty topics
            if not self._subscribers[topic]:
                del self._subscribers[topic]
    
    async def _cleanup(self) -> None:
        """
        Clean up connection resources
        """
        # Store mavlink reference before clearing
        mavlink_ref = self._mavlink
        
        # Close mavlink connection (this will close the underlying serial port)
        if mavlink_ref is not None:
            try:
                if hasattr(mavlink_ref, 'close'):
                    mavlink_ref.close()
            except Exception as e:
                logger.error(f"Error closing MAVLink connection: {e}")
            finally:
                self._mavlink = None
        
        # Close our own serial connection if it exists and is separate
        if self._connection is not None:
            try:
                # Only close if it's not the same as mavlink's connection
                if mavlink_ref and hasattr(mavlink_ref, 'port') and hasattr(mavlink_ref.port, 'ser'):
                    if self._connection != mavlink_ref.port.ser:
                        if self._connection.is_open:
                            self._connection.close()
                elif self._connection.is_open:
                    self._connection.close()
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")
            finally:
                self._connection = None
        
        self._device = None
        self._baud = None
        self._last_heartbeat_time = None
    
    def has_active_heartbeat(self, timeout_seconds: float = 10.0) -> bool:
        """
        Check if there is an active heartbeat (received within timeout)
        Args:
            timeout_seconds: Maximum seconds since last heartbeat to consider it active
        Returns:
            True if heartbeat is active, False otherwise
        """
        if self._last_heartbeat_time is None:
            return False
        
        current_time = time.time()
        time_since_last = current_time - self._last_heartbeat_time
        return time_since_last <= timeout_seconds
    
    def get_heartbeat_status(self) -> Dict[str, Any]:
        """
        Get heartbeat status information
        Returns:
            Dictionary with heartbeat status and time since last heartbeat
        """
        if self._last_heartbeat_time is None:
            return {
                "active": False,
                "time_since_last": None
            }
        
        current_time = time.time()
        time_since_last = current_time - self._last_heartbeat_time
        
        return {
            "active": time_since_last <= 10.0,
            "time_since_last": time_since_last
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get connection status
        Returns:
            Dictionary with connection status, device, baud, and heartbeat status
        """
        heartbeat_status = self.get_heartbeat_status()
        return {
            "connected": self.is_connected(),
            "device": self._device,
            "baud": self._baud,
            "heartbeat_active": heartbeat_status["active"]
        }


# Create singleton instance
fc_connection_manager = FCConnectionManager()

