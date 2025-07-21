import logging
import time
import hashlib
import os
from functools import wraps
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), '../../logs')
LOG_FILE = os.path.join(LOG_DIR, 'ui_event.log')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logger = logging.getLogger("telemetry_logger")
file_handler = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


def hash_user_id(user_id):
    return hashlib.sha256(user_id.encode()).hexdigest()[:12]


def log_ui_event(event_type, user_id, result, processing_time, error=None):
    log_entry = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": hash_user_id(user_id),
        "result": result,
        "processing_time_ms": int(processing_time * 1000),
        "error": error
    }
    logger.info(log_entry)


def telemetry_instrumentation(handler_func):
    @wraps(handler_func)
    def wrapper(self, event, *args, **kwargs):
        start = time.time()
        error = None
        try:
            result = handler_func(self, event, *args, **kwargs)
            status = "success"
            return result
        except Exception as e:
            status = "error"
            error = str(e)
            raise
        finally:
            elapsed = time.time() - start
            user_id = getattr(event, 'user_id', 'unknown')
            event_type = getattr(event, 'event_type', 'unknown')
            log_ui_event(event_type, user_id, status, elapsed, error)
    return wrapper

# Usage: decorate handler methods in AdvancedBehaviorEngine with @telemetry_instrumentation 