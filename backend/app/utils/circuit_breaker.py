"""
Circuit Breaker pattern implementation for fault tolerance
Prevents cascading failures by failing fast when a service is down
"""
import asyncio
import time
from enum import Enum
from typing import Callable, TypeVar, Any, Optional
from functools import wraps
from app.utils.logger import logger

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation, requests flow through
    OPEN = "open"          # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    def __init__(
        self,
        failure_threshold: int = 5,      # Number of failures to open circuit
        success_threshold: int = 2,       # Number of successes to close circuit (from half-open)
        timeout: float = 60.0,            # Seconds to wait before trying half-open
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception


class CircuitBreaker:
    """
    Circuit breaker for protecting external service calls
    
    Usage:
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=5))
        
        @breaker.call
        def my_function():
            # ... external service call
    """
    
    def __init__(self, config: CircuitBreakerConfig, name: str = "unnamed"):
        self.config = config
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change: float = time.time()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt half-open state"""
        if self.state != CircuitState.OPEN:
            return False
        
        if self.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.timeout
    
    def _record_success(self):
        """Record a successful call"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"Circuit breaker '{self.name}': Success in HALF_OPEN state "
                f"({self.success_count}/{self.config.success_threshold})"
            )
            
            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning(f"Circuit breaker '{self.name}': Failure in HALF_OPEN state, reopening")
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            logger.warning(
                f"Circuit breaker '{self.name}': Failure recorded "
                f"({self.failure_count}/{self.config.failure_threshold})"
            )
            
            if self.failure_count >= self.config.failure_threshold:
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state (circuit is open, fail fast)"""
        old_state = self.state
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        logger.error(
            f"🔴 Circuit breaker '{self.name}' transitioned: {old_state.value} → OPEN",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": "open",
                "failure_count": self.failure_count
            }
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state (testing recovery)"""
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = time.time()
        logger.info(
            f"🟡 Circuit breaker '{self.name}' transitioned: {old_state.value} → HALF_OPEN",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": "half_open"
            }
        )
    
    def _transition_to_closed(self):
        """Transition to CLOSED state (normal operation)"""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        logger.info(
            f"🟢 Circuit breaker '{self.name}' transitioned: {old_state.value} → CLOSED",
            extra={
                "circuit_breaker": self.name,
                "old_state": old_state.value,
                "new_state": "closed"
            }
        )
    
    def call(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for synchronous functions"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check if we should attempt reset
            if self._should_attempt_reset():
                self._transition_to_half_open()
            
            # If circuit is open, fail fast
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
                )
            
            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result
            except self.config.expected_exception as e:
                self._record_failure()
                raise
        
        return wrapper
    
    def call_async(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator for async functions"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if we should attempt reset
            if self._should_attempt_reset():
                self._transition_to_half_open()
            
            # If circuit is open, fail fast
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. Service unavailable."
                )
            
            try:
                result = await func(*args, **kwargs)
                self._record_success()
                return result
            except self.config.expected_exception as e:
                self._record_failure()
                raise
        
        return wrapper
    
    def get_state(self) -> dict:
        """Get current circuit breaker state for monitoring"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "time_since_last_change": time.time() - self.last_state_change
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and call is rejected"""
    pass


# Global circuit breakers for different services
_circuit_breakers = {}


def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name
    
    This ensures we have one circuit breaker per service
    """
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig()
        _circuit_breakers[name] = CircuitBreaker(config, name)
    
    return _circuit_breakers[name]


def get_all_circuit_breakers() -> dict:
    """Get state of all circuit breakers (for monitoring)"""
    return {
        name: breaker.get_state()
        for name, breaker in _circuit_breakers.items()
    }


# Pre-configured circuit breakers for common services
GEMINI_CIRCUIT_BREAKER = get_circuit_breaker(
    "gemini_api",
    CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0
    )
)

DATABASE_CIRCUIT_BREAKER = get_circuit_breaker(
    "database",
    CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=1,
        timeout=30.0
    )
)

