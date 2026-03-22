"""
FetchHandler: Centralized, robust HTTP request handling with retry logic.

This is a one-stop shop for HTTP GET requests with retries, backoff, 
and optional pacing so the pipeline can run unattended and tolerate transient failures.

Features:
- Configurable retries, backoff, and timeouts
- Handles 429 (rate limit), 5xx (server errors), timeouts, connection errors
- Optional delay between requests to reduce server load
- Designed for autonomous pipeline execution (no manual intervention needed)
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import requests
from requests.exceptions import (
    HTTPError,
    Timeout,
    ConnectionError,
    RequestException,
)

from src.pipeline.terminal_output import TerminalOutput

logger = logging.getLogger(__name__)


@dataclass
class FetchHandlerConfig:
    """Configuration for FetchHandler."""
    timeout: int = 60                    # Request timeout in seconds
    max_retries: int = 8                 # Max retry attempts per request
    initial_backoff: float = 2.0         # Initial backoff in seconds
    max_backoff: float = 120.0           # Max backoff cap in seconds
    backoff_multiplier: float = 2.0      # Exponential backoff multiplier
    delay_between_requests: float = 0.5  # Delay between successful requests (seconds) used for pacing the pipeline (throttling)
    retry_on_status: tuple = field(default_factory=lambda: (429, 500, 502, 503, 504))


class FetchHandler:
    """
    Handles HTTP requests with retry logic for autonomous pipeline execution.
    
    Usage:
        handler = FetchHandler(config)
        response = handler.get(url, params=params)
        data = response.json()
    """

    def __init__(self, config: Optional[FetchHandlerConfig] = None):
        self.config = config or FetchHandlerConfig()
        self._last_request_time: float = 0.0

    def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        context: str = "",
    ) -> requests.Response:
        """
        Perform a GET request with automatic retry on transient failures.
        
        Args:
            url: Request URL
            params: Query parameters
            context: Optional context string for logging (e.g. "page 5/100")
        
        Returns:
            requests.Response on success
        
        Raises:
            RequestException: After max retries exhausted
        """
        cfg = self.config
        attempt = 0
        last_exception: Optional[Exception] = None

        while attempt < cfg.max_retries:
            # Delay between requests (after the first)
            if attempt == 0 and cfg.delay_between_requests > 0:
                elapsed = time.time() - self._last_request_time
                if elapsed < cfg.delay_between_requests:
                    time.sleep(cfg.delay_between_requests - elapsed)

            attempt += 1
            try:
                response = requests.get(url, params=params, timeout=cfg.timeout)
                self._last_request_time = time.time()

                # Check for retryable HTTP status
                if response.status_code in cfg.retry_on_status:
                    wait = self._backoff(attempt)
                    self._log_retry(
                        f"{response.status_code} server error",
                        attempt,
                        wait,
                        context,
                    )
                    time.sleep(wait)
                    continue

                # Raise for other HTTP errors (4xx except 429)
                response.raise_for_status()
                return response

            except Timeout as e:
                last_exception = e
                wait = self._backoff(attempt)
                self._log_retry("Timeout", attempt, wait, context)
                time.sleep(wait)

            except ConnectionError as e:
                last_exception = e
                wait = self._backoff(attempt)
                self._log_retry("Connection error", attempt, wait, context)
                time.sleep(wait)

            except HTTPError as e:
                # Non-retryable HTTP error (e.g. 400, 401, 404)
                raise

            except RequestException as e:
                last_exception = e
                wait = self._backoff(attempt)
                self._log_retry(f"Request error: {type(e).__name__}", attempt, wait, context)
                time.sleep(wait)

        # Exhausted retries
        msg = f"Max retries ({cfg.max_retries}) exhausted for {url}"
        if context:
            msg += f" [{context}]"
        logger.error(msg)
        TerminalOutput.info(f"  FAILED after {cfg.max_retries} attempts: {context or url}", indent=1)
        if last_exception:
            raise last_exception
        raise RequestException(msg)

    def _backoff(self, attempt: int) -> float:
        """Calculate backoff time with exponential increase and cap."""
        cfg = self.config
        wait = cfg.initial_backoff * (cfg.backoff_multiplier ** (attempt - 1))
        return min(wait, cfg.max_backoff)

    def _log_retry(self, reason: str, attempt: int, wait: float, context: str) -> None:
        """Log a retry attempt."""
        cfg = self.config
        ctx = f" [{context}]" if context else ""
        msg = f"{reason}{ctx}, retry {attempt}/{cfg.max_retries} in {wait:.1f}s..."
        logger.warning(msg)
        TerminalOutput.info(f"  {msg}", indent=1)
