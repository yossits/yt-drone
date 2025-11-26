"""
Monitor Manager - ניהול 3 monitors לפי תדירות
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable, Any

from app.core.websocket import websocket_manager

logger = logging.getLogger(__name__)


class MonitorManager:
    """
    מנהל 3 monitors: fast (5s), slow (60s), static (once)
    """
    
    def __init__(self):
        """אתחול המנהל"""
        self.monitors: Dict[str, Dict] = {}  # topic -> {task, interval, data_function}
        self.static_sent: set = set()  # topics סטטיים שכבר נשלחו
    
    def register_monitor(
        self,
        topic: str,
        data_function: Callable[[], Dict[str, Any]],
        interval: Optional[float] = None
    ) -> bool:
        """
        רישום monitor חדש
        Args:
            topic: שם ה-topic (למשל: "fast_info")
            data_function: פונקציה שמחזירה dict עם הנתונים
            interval: מרווח זמן בשניות (None = חד פעמי)
        Returns:
            True אם הרישום הצליח, False אם כבר קיים
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
        הפעלת כל ה-monitors
        """
        for topic, monitor_info in self.monitors.items():
            if monitor_info["task"] is not None:
                continue  # כבר רץ
            
            interval = monitor_info["interval"]
            
            if interval is None:
                # עדכון חד פעמי
                task = asyncio.create_task(self._send_one_time(topic))
            else:
                # עדכון תקופתי
                task = asyncio.create_task(self._monitor_loop(topic, interval))
            
            monitor_info["task"] = task
            logger.info(f"Started monitor '{topic}' with interval: {interval}")
    
    async def stop_all(self) -> None:
        """
        עצירת כל ה-monitors
        """
        logger.info("Stopping all monitors...")
        for topic, monitor_info in self.monitors.items():
            task = monitor_info["task"]
            if task is not None and not task.done():
                logger.debug(f"Cancelling monitor '{topic}'")
                task.cancel()
                try:
                    # המתנה עם timeout כדי למנוע מצב שבו shutdown נתקע
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
        שליחת עדכון חד פעמי
        """
        if topic in self.static_sent:
            logger.debug(f"Static info for '{topic}' already sent, skipping")
            return  # כבר נשלח
        
        try:
            monitor_info = self.monitors.get(topic)
            if not monitor_info:
                logger.error(f"Monitor '{topic}' not found in registered monitors")
                return
            
            data_function = monitor_info["data_function"]
            
            # איסוף נתונים
            logger.debug(f"Collecting data for static topic '{topic}'")
            data = data_function()
            if not isinstance(data, dict):
                logger.error(f"Data function for '{topic}' did not return a dict, got: {type(data)}")
                return
            
            data["timestamp"] = datetime.now().isoformat()
            
            # המתנה קצרה כדי שה-clients יספיקו לעשות subscribe
            await asyncio.sleep(1)
            
            # שליחה דרך WebSocket
            sent_count = await websocket_manager.broadcast(topic, data)
            
            # עדכון static_sent רק אחרי שליחה מוצלחת
            if sent_count >= 0:  # גם אם אין subscribers, זה נחשב הצלחה
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
        לולאת monitoring תקופתי
        """
        logger.info(f"Starting monitor loop for '{topic}' with interval: {interval}s")
        
        # שליחה מיד בהתחלה (לפני ה-sleep הראשון)
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
            
            # המתנה קצרה כדי שה-clients יספיקו לעשות subscribe
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
            # ממשיכים גם אם יש שגיאה בהתחלה
        
        # עכשיו הלולאה הרגילה
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                monitor_info = self.monitors.get(topic)
                if not monitor_info:
                    logger.error(f"Monitor '{topic}' not found in registered monitors, stopping loop")
                    break
                
                data_function = monitor_info["data_function"]
                
                # איסוף נתונים
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
                
                # המתנה לפני העדכון הבא
                await asyncio.sleep(interval)
                
                # שליחה דרך WebSocket
                sent_count = await websocket_manager.broadcast(topic, data)
                
                # איפוס מונה שגיאות אחרי שליחה מוצלחת
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
                # במקרה של שגיאה, ממתינים לפני ניסיון נוסף
                await asyncio.sleep(interval)


# יצירת instance גלובלי
monitor_manager = MonitorManager()

