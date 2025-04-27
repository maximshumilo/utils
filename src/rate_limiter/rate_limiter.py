import threading
import time
from functools import wraps
from typing import Callable, TypeAlias
from weakref import WeakKeyDictionary

_ObjType: TypeAlias = Callable | "RateLimiter"


class RateLimiter:
    """
    A class for limiting the frequency of function calls based on maximum requests per second (RPS)
    or minimum delay between calls. Supports both decorator-based and direct rate-limiting.

    The class can be configured with a default RPS or delay, and provides two decorator methods:
    - set_by_rps: Limits calls based on maximum requests per second.
    - set_by_delay: Limits calls based on minimum delay between calls.

    Attributes
    ----------
    _locks : WeakKeyDictionary
        Stores locks for each function or object to ensure thread-safety.
    _last_calls : WeakKeyDictionary
        Stores timestamps of the last calls to calculate elapsed time.
    _default_interval : float
        The default interval (in seconds) for rate-limiting when used as a decorator without arguments.
    """

    def __init__(self, rps: float | None = None, delay: float | None = None):
        """
        Initializes the RateLimiter with an optional default RPS or delay.

        Parameters
        ----------
        rps : float, optional
            Maximum requests per second. If provided, set the default interval as 1/rps.
        delay : float, optional
            Minimum delay between calls (in seconds). If provided, set the default interval.
        """
        self._set_default_interval(rps=rps, delay=delay)
        self._locks = WeakKeyDictionary()
        self._last_calls = WeakKeyDictionary()

    def __call__(self, func: Callable) -> Callable:
        """
        Allows using the RateLimiter as a decorator with default settings.

        Parameters
        ----------
        func : Callable
            The function to be rate-limited.

        Returns
        -------
        Callable
            The wrapped function with rate-limiting applied.

        Raises
        ------
        ValueError
            If no default interval is set (neither rps nor delay provided in __init__).
        """
        if self._default_interval is None:
            raise ValueError("No default rate limit set. Use set_by_rps or set_by_delay.")
        return self._wrap_with_limit(self._default_interval)(func)

    def _set_default_interval(self, rps: float | None, delay: float | None) -> None:
        """
        Set the default interval for rate-limiting based on RPS or delay.

        Determine the default interval for the `RateLimiter` when used as a decorator
        without explicit parameters. Only one of `rps` or `delay` can be specified.

        Parameters
        ----------
        rps : float or None
            Maximum requests per second. If provided, the interval is set to `1/rps`.
            Must be a positive number. Default is None.
        delay : float or None
            Minimum delay between calls in seconds. If provided, the interval is set to
            this value. Must be a positive number. Default is None.

        Raises
        ------
        ValueError
            If both `rps` and `delay` are provided, or if either `rps` or `delay` is
            not a positive number.

        Notes
        -----
        This is an internal method used to configure the default behavior of the
        `RateLimiter`. The resulting interval is stored in `self._default_interval`.
        If neither `rps` nor `delay` is provided, `self._default_interval` is set to
        None.
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
        Decorator to limit function calls based on maximum requests per second (RPS).

        Parameters
        ----------
        max_rps : float
            Maximum number of requests per second.

        Returns
        -------
        Callable
            A decorator that applies the rate limit.

        Examples
        --------
        >>> rate_limiter = RateLimiter()
        >>> @rate_limiter.set_by_rps(max_rps=3)
        >>> def my_function():
        >>>     print("Called")
        """
        if not isinstance(max_rps, (int, float)) or max_rps <= 0:
            raise ValueError("max_rps must be a positive number")
        return self._wrap_with_limit(1 / max_rps)

    def set_by_delay(self, delay_sec: float) -> Callable:
        """
        Decorator to limit function calls based on the minimum delay between calls.

        Parameters
        ----------
        delay_sec : float
            Minimum delay between consecutive calls (in seconds).

        Returns
        -------
        Callable
            A decorator that applies the rate limit.

        Examples
        --------
        >>> rate_limiter = RateLimiter()
        >>> @rate_limiter.set_by_delay(delay_sec=0.5)
        >>> def my_function():
        >>>     print("Called")
        """
        if not isinstance(delay_sec, (int, float)) or delay_sec <= 0:
            raise ValueError("delay_sec must be a positive number")
        return self._wrap_with_limit(delay_sec)

    def sleep_by_rps(self, max_rps: float) -> None:
        """
        Ensures the specified RPS interval passes before the next call to the RateLimiter object.

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
        Ensures the specified delay passes before the next call to the RateLimiter object.

        Parameters
        ----------
        delay_sec : float
            Minimum delay between calls (in seconds).
        """
        if not isinstance(delay_sec, (int, float)) or delay_sec <= 0:
            raise ValueError("delay_sec must be a positive number")
        self._wait(target_obj=self, interval_sec=delay_sec)

    def _wrap_with_limit(self, interval_sec: float) -> Callable:
        """
        Internal method to create a decorator with the specified interval.

        Parameters
        ----------
        interval_sec : float
            Time interval between function calls (in seconds).

        Returns
        -------
        Callable
            A decorator that limits the frequency of function calls.
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
        Internal method to handle waiting logic for the specified interval.

        Parameters
        ----------
        target_obj : _ObjType
            The function or object for which the rate limit is applied.
        interval_sec : float
            Time interval between consecutive calls (in seconds).
        """
        with self._locks[target_obj]:
            now = time.time()
            wait_time = interval_sec - (now - self._last_calls[target_obj])
            if wait_time > 0:
                time.sleep(wait_time)
            self._last_calls[target_obj] = time.time()
