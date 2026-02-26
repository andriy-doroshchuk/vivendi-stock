"""Rate limiting utility for API requests."""
import time
import logging
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimiter:
    """Thread-safe rate limiter for API calls."""

    min_interval: float = 3.0
    _last_call: float = field(default_factory=lambda: 0.0, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    def wait(self) -> None:
        with self._lock:
            elapsed = time.time() - self._last_call
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                logger.debug('Rate limit: sleeping for %.2fs', sleep_time)
                time.sleep(sleep_time)
            self._last_call = time.time()
