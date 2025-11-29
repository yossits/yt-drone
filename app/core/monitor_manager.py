"""
Monitor Manager - managing 3 monitors by frequency
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, Any

from app.core.websocket import websocket_manager

logger = logging.getLogger(__name__)


class MonitorManager:
    """
    Manages 3 monitors: fast (5s), slow (60s), static (once)
    """
    
    def __init__(self):
        """Initialize the manager"""
        self.monitors: Dict[str, Dict] = {}  # topic -> {task, interval, data_function}
        self.static_sent: set = set()  # static topics that have already been sent
    
    def register_monitor(
        self,
        topic: str,
        data_function: Callable[[], Dict[str, Any]],
        interval: Optional[float] = None
    ) -> bool:
        """
        Register a new monitor
        Args:
            topic: Topic name (e.g., "fast_info")
            data_function: Function that returns dict with data
            interval: Time interval in seconds (None = one-time)
        Returns:
            True if registration succeeded, False if already exists
        """
        if topic in self.monitors:
            logger.warning(f"Monitor '{topic}' already registered")
            return False
        
        self.monitors[topic] = {
            "data_function": data_function,
            "interval": interval,
            "task": None
        }
        logger.info(f"Registered monitor '{topic}' with interval: {interval}")
        return True
    
    async def start_all(self) -> None:
        """
        Start all monitors
        """
        for topic, monitor_info in self.monitors.items():
            if monitor_info["task"] is not None:
                continue  # already running
            
            interval = monitor_info["interval"]
            
            if interval is None:
                # one-time update
                task = asyncio.create_task(self._send_one_time(topic))
            else:
                # periodic update
                task = asyncio.create_task(self._monitor_loop(topic, interval))
            
            monitor_info["task"] = task
            logger.info(f"Started monitor '{topic}' with interval: {interval}")
    
    async def stop_all(self) -> None:
        """
        Stop all monitors
        """
        logger.info("Stopping all monitors...")
        for topic, monitor_info in self.monitors.items():
            task = monitor_info["task"]
            if task is not None and not task.done():
                logger.debug(f"Cancelling monitor '{topic}'")
                task.cancel()
                try:
                    # Wait with timeout to prevent shutdown from getting stuck
                    await asyncio.wait_for(task, timeout=5.0)
                    logger.debug(f"Monitor '{topic}' stopped successfully")
                except asyncio.TimeoutError:
                    logger.warning(f"Monitor '{topic}' did not stop within timeout (5s)")
                except asyncio.CancelledError:
                    logger.debug(f"Monitor '{topic}' cancelled successfully")
                except Exception as e:
                    logger.warning(f"Unexpected error while stopping monitor '{topic}': {e}")
                finally:
                    monitor_info["task"] = None
                    logger.info(f"Stopped monitor '{topic}'")
        
        logger.info("All monitors stopped")
    
    async def _send_one_time(self, topic: str) -> None:
        """
        Send one-time update
        """
        if topic in self.static_sent:
            logger.debug(f"Static info for '{topic}' already sent, skipping")
            return  # already sent
        
        try:
            monitor_info = self.monitors.get(topic)
            if not monitor_info:
                logger.error(f"Monitor '{topic}' not found in registered monitors")
                return
            
            data_function = monitor_info["data_function"]
            
            # Collect data
            logger.debug(f"Collecting data for static topic '{topic}'")
            data = data_function()
            if not isinstance(data, dict):
                logger.error(f"Data function for '{topic}' did not return a dict, got: {type(data)}")
                return
            
            data["timestamp"] = datetime.now().isoformat()
            
            # Short wait so clients have time to subscribe
            await asyncio.sleep(1)
            
            # Send via WebSocket
            sent_count = await websocket_manager.broadcast(topic, data)
            
            # Update static_sent only after successful send
            if sent_count >= 0:  # Even if there are no subscribers, this is considered success
                self.static_sent.add(topic)
                logger.info(f"Sent one-time update for '{topic}' to {sent_count} connections")
            else:
                logger.warning(f"Failed to send one-time update for '{topic}'")
                
        except KeyError as e:
            logger.error(f"Monitor '{topic}' configuration error: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Error sending one-time update for '{topic}': {e}", exc_info=True)
    
    async def _monitor_loop(self, topic: str, interval: float) -> None:
        """
        Periodic monitoring loop
        """
        logger.info(f"Starting monitor loop for '{topic}' with interval: {interval}s")
        
        # Send immediately at start (before the first sleep)
        try:
            monitor_info = self.monitors.get(topic)
            if not monitor_info:
                logger.error(f"Monitor '{topic}' not found in registered monitors")
                return
            
            data_function = monitor_info["data_function"]
            
            logger.debug(f"Collecting initial data for topic '{topic}'")
            data = data_function()
            if not isinstance(data, dict):
                logger.error(f"Data function for '{topic}' did not return a dict, got: {type(data)}")
                return
            
            data["timestamp"] = datetime.now().isoformat()
            
            # Short wait so clients have time to subscribe
            await asyncio.sleep(1)
            
            sent_count = await websocket_manager.broadcast(topic, data)
            
            if sent_count > 0:
                logger.debug(f"Broadcasted '{topic}' to {sent_count} connections (initial)")
            else:
                logger.debug(f"No connections for topic '{topic}' (initial)")
        except KeyError as e:
            logger.error(f"Monitor '{topic}' configuration error in initial broadcast: {e}", exc_info=True)
            return
        except Exception as e:
            logger.error(f"Error in initial broadcast for '{topic}': {e}", exc_info=True)
            # Continue even if there's an error at the start
        
        # Now the regular loop
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                monitor_info = self.monitors.get(topic)
                if not monitor_info:
                    logger.error(f"Monitor '{topic}' not found in registered monitors, stopping loop")
                    break
                
                data_function = monitor_info["data_function"]
                
                # Collect data
                logger.debug(f"Collecting data for topic '{topic}'")
                data = data_function()
                if not isinstance(data, dict):
                    logger.error(f"Data function for '{topic}' did not return a dict, got: {type(data)}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many consecutive errors for '{topic}', stopping loop")
                        break
                    await asyncio.sleep(interval)
                    continue
                
                data["timestamp"] = datetime.now().isoformat()
                
                # Wait before next update
                await asyncio.sleep(interval)
                
                # Send via WebSocket
                sent_count = await websocket_manager.broadcast(topic, data)
                
                # Reset error counter after successful send
                if consecutive_errors > 0:
                    logger.info(f"Monitor '{topic}' recovered after {consecutive_errors} errors")
                    consecutive_errors = 0
                
                if sent_count > 0:
                    logger.debug(f"Broadcasted '{topic}' to {sent_count} connections")
                else:
                    logger.debug(f"No connections for topic '{topic}'")
            
            except asyncio.CancelledError:
                logger.info(f"Monitor '{topic}' cancelled")
                break
            except KeyError as e:
                logger.error(f"Monitor '{topic}' configuration error: {e}", exc_info=True)
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors for '{topic}', stopping loop")
                    break
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitor loop for '{topic}': {e}", exc_info=True)
                consecutive_errors += 1
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"Too many consecutive errors ({consecutive_errors}) for '{topic}', stopping loop")
                    break
                # In case of error, wait before next attempt
                await asyncio.sleep(interval)


# Create global instance
monitor_manager = MonitorManager()

