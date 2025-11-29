"""
WebSocket Manager for managing connections and topics
Enables centralized management of all WebSocket connections in the application
"""

from typing import Set, Dict, Optional
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and topics
    """
    
    def __init__(self):
        """Initialize the manager"""
        self.connections: Set[WebSocket] = set()
        self.topics: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, topic: Optional[str] = None) -> bool:
        """
        Connect client to WebSocket
        Args:
            websocket: WebSocket connection
            topic: Specific topic (optional)
        Returns:
            True if connection succeeded, False otherwise
        """
        try:
            await websocket.accept()
            self.connections.add(websocket)
            
            if topic:
                await self.subscribe(websocket, topic)
            
            logger.info(f"WebSocket connected. Total connections: {len(self.connections)}")
            return True
        except Exception as e:
            logger.error(f"Error connecting WebSocket: {e}")
            return False
    
    def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect client
        Args:
            websocket: WebSocket connection to disconnect
        """
        if websocket in self.connections:
            self.connections.remove(websocket)
        
        # Remove connection from all topics
        for topic in list(self.topics.keys()):
            self.topics[topic].discard(websocket)
            # Remove empty topics
            if not self.topics[topic]:
                del self.topics[topic]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.connections)}")
    
    async def subscribe(self, websocket: WebSocket, topic: str) -> bool:
        """
        Subscribe to topic
        Args:
            websocket: WebSocket connection
            topic: Topic name
        Returns:
            True if subscription succeeded
        """
        try:
            if topic not in self.topics:
                self.topics[topic] = set()
            
            self.topics[topic].add(websocket)
            logger.debug(f"WebSocket subscribed to topic: {topic}")
            return True
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
            return False
    
    def unsubscribe(self, websocket: WebSocket, topic: str) -> None:
        """
        Unsubscribe from topic
        Args:
            websocket: WebSocket connection
            topic: Topic name
        """
        if topic in self.topics:
            self.topics[topic].discard(websocket)
            # Remove empty topic
            if not self.topics[topic]:
                del self.topics[topic]
            logger.debug(f"WebSocket unsubscribed from topic: {topic}")
    
    async def send_personal_message(self, websocket: WebSocket, message: dict) -> bool:
        """
        Send message to specific connection
        Args:
            websocket: WebSocket connection
            message: Message to send (dict)
        Returns:
            True if send succeeded, False otherwise
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            return False
    
    async def broadcast(self, topic: str, data: dict) -> int:
        """
        Send update to all subscribers of topic
        Args:
            topic: Topic name
            data: Data to send
        Returns:
            Number of connections that received the message
        """
        if topic not in self.topics:
            logger.debug(f"No subscribers for topic: {topic}")
            return 0
        
        message = {
            "topic": topic,
            "data": data
        }
        
        disconnected = set()
        sent_count = 0
        
        for websocket in self.topics[topic].copy():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Error broadcasting to WebSocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for ws in disconnected:
            self.disconnect(ws)
        
        logger.debug(f"Broadcasted to {sent_count} connections for topic: {topic}")
        return sent_count
    
    async def broadcast_to_all(self, data: dict) -> int:
        """
        Send message to all connections
        Args:
            data: Data to send
        Returns:
            Number of connections that received the message
        """
        message = {
            "topic": "broadcast",
            "data": data
        }
        
        disconnected = set()
        sent_count = 0
        
        for websocket in self.connections.copy():
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Error broadcasting to all: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected connections
        for ws in disconnected:
            self.disconnect(ws)
        
        logger.debug(f"Broadcasted to {sent_count} connections")
        return sent_count
    
    def get_connection_count(self) -> int:
        """
        Returns number of active connections
        Returns:
            Number of connections
        """
        return len(self.connections)
    
    def get_topic_subscribers_count(self, topic: str) -> int:
        """
        Returns number of subscribers to topic
        Args:
            topic: Topic name
        Returns:
            Number of subscribers
        """
        return len(self.topics.get(topic, set()))
    
    def get_topics(self) -> list:
        """
        Returns list of all topics
        Returns:
            List of topics
        """
        return list(self.topics.keys())


# Create global instance of the manager
websocket_manager = WebSocketManager()

