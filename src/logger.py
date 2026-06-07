
import logging
import structlog


#========================================================================
#
#========================================================================
def setup_logging() -> None:
    
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,           # מוסיף "level": "info"
            structlog.stdlib.add_logger_name,          # מוסיף "logger": "pipeline"
            structlog.processors.TimeStamper(fmt="iso"), # מוסיף timestamp
            structlog.processors.JSONRenderer(),        # הופך הכל ל-JSON
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )


#========================================================================
#
#========================================================================
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a named structured logger."""
    return structlog.get_logger(name)