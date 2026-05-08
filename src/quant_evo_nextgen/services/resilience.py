from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

import httpx

from quant_evo_nextgen.logging_utils import log_event

T = TypeVar("T")

TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 2.0
    jitter_seconds: float = 0.1


def retry_transient(
    operation: Callable[[], T],
    *,
    operation_name: str,
    logger: logging.Logger,
    policy: RetryPolicy | None = None,
    retry_on_result: Callable[[T], bool] | None = None,
) -> T:
    effective_policy = policy or RetryPolicy()
    attempts = max(1, effective_policy.max_attempts)
    last_error: BaseException | None = None

    for attempt in range(1, attempts + 1):
        try:
            result = operation()
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as exc:
            last_error = exc
            should_retry = attempt < attempts
            log_event(
                logger,
                "external_call_exception",
                operation=operation_name,
                attempt=attempt,
                max_attempts=attempts,
                retrying=should_retry,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            if should_retry:
                _sleep_before_retry(attempt, effective_policy)
                continue
            raise

        if retry_on_result and retry_on_result(result) and attempt < attempts:
            log_event(
                logger,
                "external_call_retry",
                operation=operation_name,
                attempt=attempt,
                max_attempts=attempts,
            )
            _sleep_before_retry(attempt, effective_policy)
            continue
        return result

    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Retry operation did not return a result: {operation_name}")


def is_transient_http_status(status_code: int) -> bool:
    return status_code in TRANSIENT_STATUS_CODES


def _sleep_before_retry(attempt: int, policy: RetryPolicy) -> None:
    delay = min(policy.max_delay_seconds, policy.base_delay_seconds * (2 ** max(0, attempt - 1)))
    if policy.jitter_seconds > 0:
        delay += random.uniform(0, policy.jitter_seconds)
    time.sleep(delay)
