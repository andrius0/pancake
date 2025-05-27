import logging
import sys
import json
from typing import Any, Dict
from datetime import datetime

class TemporalContextFilter(logging.Filter):
    """Filter to add Temporal-specific context to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'temporal_context'):
            record.temporal_context = {}
        return True

def format_temporal_context(context: Dict[str, Any]) -> str:
    """Format Temporal context for logging."""
    if not context:
        return ""
    return f" [Temporal: {json.dumps(context)}]"

class TemporalFormatter(logging.Formatter):
    """Custom formatter for Temporal-aware logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add timestamp
        record.timestamp = datetime.utcnow().isoformat()
        
        # Add Temporal context if available
        temporal_context = getattr(record, 'temporal_context', {})
        temporal_str = format_temporal_context(temporal_context)
        
        # Format the message
        return f"{record.timestamp} {record.levelname} [{record.name}]{temporal_str}: {record.getMessage()}"

def setup_logging(service_name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Set up logging configuration for a service with Temporal awareness.
    Also configures the root logger so that logging from any module uses the same format.
    Args:
        service_name: Name of the service
        log_level: Logging level (default: INFO)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.handlers = []
    root_handler = logging.StreamHandler(sys.stdout)
    root_handler.setFormatter(TemporalFormatter())
    root_handler.addFilter(TemporalContextFilter())
    root_logger.addHandler(root_handler)

    # Configure service-specific logger (optional, for backward compatibility)
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers = []
    logger.addHandler(root_handler)
    logger.propagate = False
    return logger

def get_logger(service_name: str) -> logging.Logger:
    """Get a logger instance for a service."""
    return logging.getLogger(service_name)

def log_with_temporal_context(
    logger: logging.Logger,
    level: str,
    message: str,
    workflow_id: str = None,
    run_id: str = None,
    activity_id: str = None,
    task_queue: str = None,
    **kwargs: Any
) -> None:
    """
    Log a message with Temporal-specific context.
    
    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        workflow_id: ID of the current workflow
        run_id: ID of the current workflow run
        activity_id: ID of the current activity
        task_queue: Name of the task queue
        **kwargs: Additional context to include in the log
    """
    temporal_context = {
        "workflow_id": workflow_id,
        "run_id": run_id,
        "activity_id": activity_id,
        "task_queue": task_queue,
        **kwargs
    }
    # Remove None values
    temporal_context = {k: v for k, v in temporal_context.items() if v is not None}
    
    extra = {"temporal_context": temporal_context}
    log_func = getattr(logger, level.lower())
    log_func(message, extra=extra)

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
