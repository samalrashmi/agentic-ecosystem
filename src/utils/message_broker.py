"""
Simple Message Broker for Agent-to-Agent Communication

This is a simplified version that uses in-memory queues instead of MQTT
for development and testing purposes.
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Optional, Any, List
import uuid
from datetime import datetime

import aiohttp

from ..models import Message, AgentType
from .logger import get_logger


class MessageBroker:
    """Message broker for Agent-to-Agent (A2A) communication using in-memory queues."""
    
    def __init__(self):
        self.logger = get_logger("MessageBroker")
        self.subscribers: Dict[str, List[Callable[[Message], None]]] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.connected = False
        self._running = False
        
    async def connect(self) -> None:
        """Connect to the message broker."""
        try:
            self.connected = True
            self._running = True
            # Start message processing task
            asyncio.create_task(self._process_messages())
            self.logger.info("Message broker connected successfully")
        except Exception as e:
            self.logger.error(f"Failed to connect to message broker: {e}")
            raise
            
    async def disconnect(self) -> None:
        """Disconnect from the message broker."""
        self._running = False
        self.connected = False
        self.logger.info("Disconnected from message broker")
        
    async def publish_message(self, topic: str, message: Message) -> None:
        """Publish a message to a topic."""
        if not self.connected:
            self.logger.warning("Message broker not connected, message dropped")
            return
            
        try:
            await self.message_queue.put((topic, message))
            self.logger.debug(f"Published message to topic {topic}: {message.message_id}")
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            
    async def subscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """Subscribe to a topic with a callback function."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        self.logger.info(f"Subscribed to topic: {topic}")
        
    async def unsubscribe(self, topic: str, callback: Callable[[Message], None]) -> None:
        """Unsubscribe from a topic."""
        if topic in self.subscribers and callback in self.subscribers[topic]:
            self.subscribers[topic].remove(callback)
            if not self.subscribers[topic]:
                del self.subscribers[topic]
        self.logger.info(f"Unsubscribed from topic: {topic}")
        
    async def _process_messages(self) -> None:
        """Process messages from the queue and deliver to subscribers."""
        while self._running:
            try:
                # Wait for message with timeout
                topic, message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                # Deliver to subscribers
                if topic in self.subscribers:
                    for callback in self.subscribers[topic]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(message)
                            else:
                                callback(message)
                        except Exception as e:
                            self.logger.error(f"Error in subscriber callback: {e}")
                            
            except asyncio.TimeoutError:
                # Normal timeout, continue processing
                continue
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
                await asyncio.sleep(1)
                
    def get_agent_topic(self, agent_type: AgentType) -> str:
        """Get the topic name for an agent type."""
        return f"agent.{agent_type.value}"
        
    def get_broadcast_topic(self) -> str:
        """Get the broadcast topic name."""
        return "agent.broadcast"


class HTTPMessageBroker:
    """HTTP-based message broker for RESTful communication."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logger = get_logger("HTTPMessageBroker")
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def connect(self) -> None:
        """Initialize the HTTP client session."""
        self.session = aiohttp.ClientSession()
        self.logger.info("HTTP message broker initialized")
        
    async def disconnect(self) -> None:
        """Close the HTTP client session."""
        if self.session:
            await self.session.close()
        self.logger.info("HTTP message broker disconnected")
        
    async def send_message(self, endpoint: str, message: Message) -> Optional[Dict[str, Any]]:
        """Send a message via HTTP POST."""
        if not self.session:
            raise RuntimeError("HTTP message broker not connected")
            
        try:
            url = f"{self.base_url}/{endpoint}"
            async with self.session.post(
                url, 
                json=message.model_dump(),
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"HTTP request failed: {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Failed to send HTTP message: {e}")
            return None
            
    async def get_messages(self, endpoint: str) -> List[Dict[str, Any]]:
        """Get messages via HTTP GET."""
        if not self.session:
            raise RuntimeError("HTTP message broker not connected")
            
        try:
            url = f"{self.base_url}/{endpoint}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"HTTP request failed: {response.status}")
                    return []
        except Exception as e:
            self.logger.error(f"Failed to get HTTP messages: {e}")
            return []


# Global message broker instance
_message_broker: Optional[MessageBroker] = None


async def get_message_broker() -> MessageBroker:
    """Get or create the global message broker instance."""
    global _message_broker
    if _message_broker is None:
        _message_broker = MessageBroker()
        await _message_broker.connect()
    return _message_broker


async def cleanup_message_broker() -> None:
    """Cleanup the global message broker instance."""
    global _message_broker
    if _message_broker:
        await _message_broker.disconnect()
        _message_broker = None
