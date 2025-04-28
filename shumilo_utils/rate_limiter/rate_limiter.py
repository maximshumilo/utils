import threading
import time
from functools import wraps
from typing import (
    Any,
    Callable,
    TypeAlias,
    TypeVar,
)
from weakref import WeakKeyDictionary


_LockT = TypeVar("_LockT", bound=threading.Lock)
_ObjType: TypeAlias = Callable[..., Any]
_K: TypeAlias = _ObjType
_V: TypeAlias = float | _LockT
_TypedDict: TypeAlias = WeakKeyDictionary[_K, _V]


class RateLimiter:
    """
    A class for limiting function calls with thread-safe rate-limiting.

    Supports decorator-based and direct rate-limiting using RPS or delay.

    Examples (simple usage)
    --------
    >>> rate_limiter = RateLimiter(rps=5)
    >>>
    >>> @rate_limiter
    >>> def my_function():
    >>>     print("Called func")
    """

    def __init__(self, rps: float | None = None, delay: float | None = None):
        """
        Initialize with an optional default RPS or delay.

        Parameters
        ----------
        rps : float, optional
            Maximum requests per second (sets an interval as 1/rps).
        delay : float, optional
            Minimum delay between calls (in seconds).
        """
        self._set_default_interval(rps=rps, delay=delay)
        self._locks: _TypedDict = WeakKeyDictionary(dict={self: threading.Lock()})
        self._last_calls: _TypedDict = WeakKeyDictionary(dict={self: 0})

    def __call__(self, func: Callable) -> Callable:
        """
        Call rate-limiting as decorator with default settings.

        Parameters
        ----------
        func : Callable
            Function to rate-limit.

        Returns
        -------
        Callable
            Wrapped function with rate-limiting.
        """
        if self._default_interval is None:
            raise ValueError("No default rate limit set.")
        return self._wrap_with_limit(self._default_interval)(func)

    def _set_default_interval(self, rps: float | None, delay: float | None) -> None:
        """
        Set default interval based on RPS or delay.

        Parameters
        ----------
        rps : float, optional
            Maximum requests per second.
        delay : float, optional
            Minimum delay between calls.
        """
        if rps is not None and delay is not None:
            raise ValueError("Cannot specify both rps and delay")
        if rps is not None:
            if not isinstance(rps, (int, float)) or rps <= 0:
                raise ValueError("rps must be a positive number")
            self._default_interval = 1 / rps
        elif delay is not None:
            if not isinstance(delay, (int, float)) or delay <= 0:
                raise ValueError("delay must be a positive number")
            self._default_interval = delay
        else:
            self._default_interval = None

    def set_by_rps(self, max_rps: float) -> Callable:
        """
        Set to limit calls by requests per second.

        Parameters
        ----------
        max_rps : float
            Maximum requests per second.

        Returns
        -------
        Callable
            Decorator with rate-limiting.
        """
        if not isinstance(max_rps, (int, float)) or max_rps <= 0:
            raise ValueError("max_rps must be a positive number")
        return self._wrap_with_limit(1 / max_rps)

    def set_by_delay(self, delay_sec: float) -> Callable:
        """
        Set to limit calls by minimum delay.

        Parameters
        ----------
        delay_sec : float
            Minimum delay between calls (in seconds).

        Returns
        -------
        Callable
            Decorator with rate-limiting.
        """
        if not isinstance(delay_sec, (int, float)) or delay_sec <= 0:
            raise ValueError("delay_sec must be a positive number")
        return self._wrap_with_limit(delay_sec)

    def sleep_by_rps(self, max_rps: float) -> None:
        """
        Enforce rate limit by sleeping based on RPS.

        Parameters
        ----------
        max_rps : float
            Maximum requests per second.
        """
        if not isinstance(max_rps, (int, float)) or max_rps <= 0:
            raise ValueError("max_rps must be a positive number")
        self._wait(target_obj=self, interval_sec=1 / max_rps)

    def sleep_by_delay(self, delay_sec: float) -> None:
        """
        Enforce rate limit by sleeping for specified delay.

        Parameters
        ----------
        delay_sec : float
            Delay between calls (in seconds).
        """
        if not isinstance(delay_sec, (int, float)) or delay_sec <= 0:
            raise ValueError("delay_sec must be a positive number")
        self._wait(target_obj=self, interval_sec=delay_sec)

    def _wrap_with_limit(self, interval_sec: float) -> Callable:
        """
        Wrap function to enforce a minimum interval between calls.

        Parameters
        ----------
        interval_sec : float
            The interval between calls.

        Returns
        -------
        Callable
            Decorator with rate-limiting.
        """

        def decorator(func: Callable) -> Callable:
            self._locks.setdefault(func, threading.Lock())
            self._last_calls.setdefault(func, 0.0)

            @wraps(func)
            def wrapper(*args, **kwargs):
                self._wait(target_obj=func, interval_sec=interval_sec)
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def _wait(self, target_obj: _ObjType, interval_sec: float) -> None:
        """
        Wait to enforce a minimum interval between calls.

        Parameters
        ----------
        target_obj : _ObjType
            Object to apply rate-limiting to.
        interval_sec : float
            The interval between calls.
        """
        with self._locks[target_obj]:
            now = time.time()
            wait_time = interval_sec - (now - self._last_calls[target_obj])
            if wait_time > 0:
                time.sleep(wait_time)
            self._last_calls[target_obj] = time.time()
