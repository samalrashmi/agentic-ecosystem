import logging
import structlog
import sys
from typing import Optional
from datetime import datetime
import json
import os


def configure_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None
):
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    if log_file:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            filename=log_file,
            format="%(message)s"
        )
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            stream=sys.stdout,
            format="%(message)s"
        )
    
    # Configure processors based on format type
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if format_type == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


class AgentLogger:
    """Specialized logger for agent activities."""
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.logger = get_logger(f"{agent_type}_agent").bind(
            agent_id=agent_id,
            agent_type=agent_type
        )
    
    def log_message_received(self, message_id: str, from_agent: str, message_type: str):
        """Log when a message is received."""
        self.logger.info(
            "Message received",
            message_id=message_id,
            from_agent=from_agent,
            message_type=message_type,
            event_type="message_received"
        )
    
    def log_message_sent(self, message_id: str, to_agent: str, message_type: str):
        """Log when a message is sent."""
        self.logger.info(
            "Message sent",
            message_id=message_id,
            to_agent=to_agent,
            message_type=message_type,
            event_type="message_sent"
        )
    
    def log_task_started(self, task_description: str, project_id: str):
        """Log when a task is started."""
        self.logger.info(
            "Task started",
            task_description=task_description,
            project_id=project_id,
            event_type="task_started"
        )
    
    def log_task_completed(self, task_description: str, project_id: str, duration: float):
        """Log when a task is completed."""
        self.logger.info(
            "Task completed",
            task_description=task_description,
            project_id=project_id,
            duration_seconds=duration,
            event_type="task_completed"
        )
    
    def log_error(self, error_message: str, context: Optional[dict] = None):
        """Log an error with context."""
        self.logger.error(
            "Agent error",
            error_message=error_message,
            context=context or {},
            event_type="error"
        )
    
    def log_artifact_created(self, artifact_id: str, artifact_type: str, project_id: str):
        """Log when an artifact is created."""
        self.logger.info(
            "Artifact created",
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            project_id=project_id,
            event_type="artifact_created"
        )


# Initialize logging configuration
configure_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format_type=os.getenv("LOG_FORMAT", "json")
)
