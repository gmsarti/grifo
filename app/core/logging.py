import logging
import json
import time
import sys
from contextlib import contextmanager
from typing import Optional, Any

class JsonFormatter(logging.Formatter):
    """Formats log records as JSON."""
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "duration"):
            log_record["duration_seconds"] = record.duration
        if hasattr(record, "metadata"):
            log_record["metadata"] = record.metadata
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
def timed_process(process_name: str, logger: Optional[logging.Logger] = None, metadata: Optional[dict] = None):
    """
    Context manager to log the duration of a process.
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
