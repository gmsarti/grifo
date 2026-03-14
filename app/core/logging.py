import logging
import json
import time
import sys
from contextlib import contextmanager
from typing import Optional, Any
from contextvars import ContextVar

# Context to store hierarchical identifiers
log_context: ContextVar[dict] = ContextVar("log_context", default={})

class JsonFormatter(logging.Formatter):
    """Formats log records as JSON, automatically including context metadata."""
    def format(self, record):
        # Base record
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Merge static record attributes
        if hasattr(record, "duration"):
            log_record["duration_seconds"] = record.duration
        
        # Automatic Context Enrichment
        context = log_context.get()
        metadata = getattr(record, "metadata", {}) or {}
        
        # Combine hierarchy from context and explicit metadata
        combined_metadata = {**context, **metadata}
        if combined_metadata:
            log_record["metadata"] = combined_metadata
            
        return json.dumps(log_record)

def setup_logging(level=logging.INFO):
    """Configures the root logger with JSON formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    
    root = logging.getLogger()
    root.setLevel(level)
    # Remove existing handlers to avoid duplicates
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.addHandler(handler)

def get_logger(name: str):
    return logging.getLogger(name)

@contextmanager
def set_log_context(user_id: Optional[str] = None, project_id: Optional[str] = None, thread_id: Optional[str] = None):
    """Context manager to set logging context variables."""
    token = log_context.set({
        "user_id": user_id,
        "project_id": project_id,
        "thread_id": thread_id
    })
    try:
        yield
    finally:
        log_context.reset(token)

@contextmanager
def timed_process(process_name: str, logger: Optional[logging.Logger] = None, metadata: Optional[dict] = None):
    """
    Context manager to log the duration of a process.
    Metadata is merged with the current log_context.
    """
    _logger = logger or get_logger("timed_process")
    start_time = time.perf_counter()
    _logger.info(f"Starting process: {process_name}", extra={"metadata": metadata})
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        _logger.info(
            f"Finished process: {process_name}",
            extra={"duration": duration, "metadata": metadata}
        )

# Initialize on import
setup_logging()
