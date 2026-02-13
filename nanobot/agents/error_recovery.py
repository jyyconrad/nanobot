"""Error recovery mechanisms for resilience."""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from loguru import logger


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5        # Failures before opening
    timeout: float = 60.0            # Seconds to wait before half-open
    success_threshold: int = 2        # Successes needed to close


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.

    Tracks failures and opens the circuit when threshold is exceeded.
    Allows recovery testing with half-open state.
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            RuntimeError: If circuit is open
            Exception: If function raises an exception
        """
        state = await self.get_state()

        if state == CircuitState.OPEN:
            raise RuntimeError(
                f"Circuit breaker {self.name} is OPEN. "
                f"Rejecting call to prevent cascading failure."
            )

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Record success
            await self._record_success()
            return result

        except Exception as e:
            # Record failure
            await self._record_failure()
            raise

    async def get_state(self) -> CircuitState:
        """
        Get current circuit state.

        Returns:
            Current circuit state
        """
        async with self._lock:
            # Check if we should transition to half-open
            if (
                self._state == CircuitState.OPEN
                and self._last_failure_time
                and (time.time() - self._last_failure_time) > self.config.timeout
            ):
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0
                logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")

            return self._state

    async def _record_success(self):
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1

                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info(f"Circuit breaker {self.name} transitioned to CLOSED")

            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0  # Reset failures on success

    async def _record_failure(self):
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open, go back to open
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} transitioned to OPEN (half-open failure)")

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        f"Circuit breaker {self.name} transitioned to OPEN "
                        f"({self._failure_count} failures)"
                    )

    async def reset(self):
        """Reset circuit breaker to closed state."""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker {self.name} reset to CLOSED")

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
        }


class RetryPolicy:
    """
    Retry policy with exponential backoff and jitter.

    Features:
    - Configurable max retries
    - Exponential backoff
    - Jitter to avoid thundering herd
    - Retry on specific exceptions
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry policy.

        Args:
            max_retries: Maximum retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Backoff multiplier
            jitter: Add random jitter to delays
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    async def execute(
        self,
        func: Callable,
        *args,
        retry_on: Optional[List[type]] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments
            retry_on: Exception types to retry on
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if attempt >= self.max_retries:
                    logger.error(
                        f"Function {func.__name__} failed after {self.max_retries} retries: {e}"
                    )
                    raise

                if retry_on and not isinstance(e, tuple(retry_on)):
                    logger.error(f"Function {func.__name__} raised non-retryable exception: {e}")
                    raise

                # Calculate delay
                delay = self._calculate_delay(attempt)

                logger.warning(
                    f"Function {func.__name__} failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                    f"retrying in {delay:.2f}s: {e}"
                )

                await asyncio.sleep(delay)

        # Should not reach here, but for type safety
        assert last_exception is not None
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt."""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)

        # Add jitter
        if self.jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)

        return delay


class TimeoutHandler:
    """
    Timeout handler for long-running operations.

    Provides configurable timeouts with graceful cleanup.
    """

    def __init__(self, default_timeout: float = 300.0):
        """
        Initialize timeout handler.

        Args:
            default_timeout: Default timeout in seconds
        """
        self.default_timeout = default_timeout

    async def execute(
        self,
        func: Callable,
        *args,
        timeout: Optional[float] = None,
        on_timeout: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with timeout.

        Args:
            func: Function to execute
            *args: Positional arguments
            timeout: Timeout in seconds (uses default if None)
            on_timeout: Callback to execute on timeout
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            TimeoutError: If timeout exceeded
            Exception: If function raises an exception
        """
        timeout = timeout or self.default_timeout

        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            else:
                # Run in thread pool for sync functions
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *args, **kwargs),
                    timeout=timeout
                )

            return result

        except asyncio.TimeoutError:
            logger.error(f"Function {func.__name__} timed out after {timeout}s")

            # Execute timeout callback
            if on_timeout:
                if asyncio.iscoroutinefunction(on_timeout):
                    await on_timeout()
                else:
                    on_timeout()

            raise TimeoutError(f"Function {func.__name__} timed out after {timeout}s")


class ErrorRecoveryManager:
    """
    Combined error recovery manager.

    Integrates circuit breaker, retry, and timeout mechanisms
    for comprehensive error handling.
    """

    def __init__(self):
        """Initialize error recovery manager."""
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._retry_policies: Dict[str, RetryPolicy] = {}
        self._timeout_handlers: Dict[str, TimeoutHandler] = {}

    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker.

        Args:
            name: Circuit breaker name
            config: Circuit breaker configuration

        Returns:
            Circuit breaker instance
        """
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = CircuitBreaker(name, config)

        return self._circuit_breakers[name]

    def get_retry_policy(
        self,
        name: str,
        **kwargs
    ) -> RetryPolicy:
        """
        Get or create retry policy.

        Args:
            name: Retry policy name
            **kwargs: Retry policy parameters

        Returns:
            Retry policy instance
        """
        if name not in self._retry_policies:
            self._retry_policies[name] = RetryPolicy(**kwargs)

        return self._retry_policies[name]

    def get_timeout_handler(
        self,
        name: str,
        timeout: Optional[float] = None
    ) -> TimeoutHandler:
        """
        Get or create timeout handler.

        Args:
            name: Timeout handler name
            timeout: Default timeout

        Returns:
            Timeout handler instance
        """
        if name not in self._timeout_handlers:
            self._timeout_handlers[name] = TimeoutHandler(timeout or 300.0)

        return self._timeout_handlers[name]

    async def execute_with_protection(
        self,
        func: Callable,
        *args,
        circuit_breaker: Optional[str] = None,
        retry_policy: Optional[str] = None,
        timeout_handler: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with all protection mechanisms.

        Args:
            func: Function to execute
            *args: Positional arguments
            circuit_breaker: Circuit breaker name
            retry_policy: Retry policy name
            timeout_handler: Timeout handler name
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If any protection mechanism triggers
        """
        # Wrap with circuit breaker
        if circuit_breaker:
            cb = self.get_circuit_breaker(circuit_breaker)
            func = lambda *a, **k: cb.call(func, *a, **k)

        # Wrap with timeout
        if timeout_handler:
            th = self.get_timeout_handler(timeout_handler)
            func = lambda *a, **k: th.execute(func, *a, **k)

        # Wrap with retry
        if retry_policy:
            rp = self.get_retry_policy(retry_policy)
            return await rp.execute(func, *args, **kwargs)
        else:
            # Execute directly
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
