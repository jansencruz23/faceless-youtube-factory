"""
Structured JSON logging configuration.
Uses structlog for consistent, parseable log output.
"""
import structlog
import logging
import sys
from typing import Any, Dict, Optional
import structlog
from structlog.types import EventDict, Processor
from app.config import settings


def add_app_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict
) -> EventDict:
    """Add application context to all log entries."""
    event_dict["app"] = settings.app_name
    return event_dict


def configure_logging() -> None:
     """
    Configure structlog for JSON logging.
    
    Call this once during application startup.
    Produces JSON output in production, colored console in development.
    """
    # Shared processor for all loggers
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info
    ]

    if settings.debug:
        # Development: colored console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: JSON output to stderr
        processors = shared_processors + [
            structlog.processors.JSONRenderer()
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.debug else logging.DEBUG
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """
    Get a configured logger instance.
    
    Args:
        name: Optional logger name for context.
    
    Returns:
        A structlog BoundLogger with the specified name.
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Processing started", project_id=project_id)
    """
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(name=name)
    return logger


def bind_context(**kwargs: Any) -> None:
     """
    Bind context variables to all subsequent log entries.
    
    Useful for request-scoped context like user_id, project_id.
    
    Usage:
        bind_context(user_id=user_id, project_id=project_id)
        logger.info("Operation completed")  # Includes user_id & project_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()