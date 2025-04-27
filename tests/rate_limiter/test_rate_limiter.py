import time
import threading
import sys
import os
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from shumilo_utils.rate_limiter.rate_limiter import RateLimiter


def test_init_default():
    """Test initialization with default parameters."""
    rate_limiter = RateLimiter()
    assert rate_limiter._default_interval is None


def test_init_with_rps():
    """Test initialization with RPS parameter."""
    rps = 5.0
    rate_limiter = RateLimiter(rps=rps)
    assert rate_limiter._default_interval == 1/rps


def test_init_with_delay():
    """Test initialization with delay parameter."""
    delay = 0.2
    rate_limiter = RateLimiter(delay=delay)
    assert rate_limiter._default_interval == delay


def test_init_with_both_rps_and_delay():
    """Test initialization with both RPS and delay parameters raises ValueError."""
    with pytest.raises(ValueError):
        RateLimiter(rps=5.0, delay=0.2)


@pytest.mark.parametrize("invalid_rps", [-1.0, 0])
def test_init_with_invalid_rps(invalid_rps):
    """Test initialization with invalid RPS parameter raises ValueError."""
    with pytest.raises(ValueError):
        RateLimiter(rps=invalid_rps)


@pytest.mark.parametrize("invalid_delay", [-0.1, 0])
def test_init_with_invalid_delay(invalid_delay):
    """Test initialization with invalid delay parameter raises ValueError."""
    with pytest.raises(ValueError):
        RateLimiter(delay=invalid_delay)

def test_call_without_default():
    """Test __call__ without default interval raises ValueError."""
    rate_limiter = RateLimiter()
    with pytest.raises(ValueError):
        @rate_limiter
        def func():
            pass


def test_call_with_default():
    """Test __call__ with default interval."""
    rate_limiter = RateLimiter(rps=10.0)

    @rate_limiter
    def func():
        return "called"

    assert func() == "called"


def test_set_by_rps():
    """Test set_by_rps decorator."""
    rate_limiter = RateLimiter()

    @rate_limiter.set_by_rps(10.0)
    def func():
        return "called"

    assert func() == "called"


@pytest.mark.parametrize("invalid_rps", [-1.0, 0])
def test_set_by_rps_invalid(invalid_rps):
    """Test set_by_rps with invalid RPS raises ValueError."""
    rate_limiter = RateLimiter()
    with pytest.raises(ValueError):
        rate_limiter.set_by_rps(invalid_rps)


def test_set_by_delay():
    """Test set_by_delay decorator."""
    rate_limiter = RateLimiter()

    @rate_limiter.set_by_delay(0.1)
    def func():
        return "called"

    assert func() == "called"


@pytest.mark.parametrize("invalid_delay", [-0.1, 0])
def test_set_by_delay_invalid(invalid_delay):
    """Test set_by_delay with invalid delay raises ValueError."""
    rate_limiter = RateLimiter()
    with pytest.raises(ValueError):
        rate_limiter.set_by_delay(invalid_delay)

def test_rate_limiting_by_rps():
    """Test actual rate limiting by RPS."""
    rate_limiter = RateLimiter()
    max_rps = 5.0
    interval = 1 / max_rps

    @rate_limiter.set_by_rps(max_rps)
    def func():
        return time.time()

    # Call the function multiple times and measure the time between calls
    times = []
    for _ in range(3):
        times.append(func())

    # Check that the time between calls is at least the expected interval
    for i in range(1, len(times)):
        assert times[i] - times[i-1] >= interval * 0.9  # Allow for small timing variations


def test_rate_limiting_by_delay():
    """Test actual rate limiting by delay."""
    rate_limiter = RateLimiter()
    delay = 0.2

    @rate_limiter.set_by_delay(delay)
    def func():
        return time.time()

    # Call the function multiple times and measure the time between calls
    times = []
    for _ in range(3):
        times.append(func())

    # Check that the time between calls is at least the expected delay
    for i in range(1, len(times)):
        assert times[i] - times[i-1] >= delay * 0.9  # Allow for small timing variations

def test_sleep_by_rps():
    """Test sleep_by_rps method."""
    rate_limiter = RateLimiter()
    max_rps = 5.0
    interval = 1 / max_rps

    # Initialize the locks and last_calls for the RateLimiter instance
    rate_limiter._locks.setdefault(rate_limiter, threading.Lock())
    rate_limiter._last_calls.setdefault(rate_limiter, 0.0)

    # Call sleep_by_rps multiple times and measure the time between calls
    times = []
    # First call to initialize
    rate_limiter.sleep_by_rps(max_rps)

    for _ in range(3):
        rate_limiter.sleep_by_rps(max_rps)
        times.append(time.time())

    # Check that the time between calls is at least the expected interval
    for i in range(1, len(times)):
        assert times[i] - times[i-1] >= interval * 0.9  # Allow for small timing variations


@pytest.mark.parametrize("invalid_rps", [-1.0, 0])
def test_sleep_by_rps_invalid(invalid_rps):
    """Test sleep_by_rps with invalid RPS raises ValueError."""
    rate_limiter = RateLimiter()
    with pytest.raises(ValueError):
        rate_limiter.sleep_by_rps(invalid_rps)


def test_sleep_by_delay():
    """Test sleep_by_delay method."""
    rate_limiter = RateLimiter()
    delay = 0.2

    # Initialize the locks and last_calls for the RateLimiter instance
    rate_limiter._locks.setdefault(rate_limiter, threading.Lock())
    rate_limiter._last_calls.setdefault(rate_limiter, 0.0)

    # First call to initialize
    rate_limiter.sleep_by_delay(delay)

    # Call sleep_by_delay multiple times and measure the time between calls
    times = []
    for _ in range(3):
        rate_limiter.sleep_by_delay(delay)
        times.append(time.time())

    # Check that the time between calls is at least the expected delay
    for i in range(1, len(times)):
        assert times[i] - times[i-1] >= delay * 0.9  # Allow for small timing variations


@pytest.mark.parametrize("invalid_delay", [-0.1, 0])
def test_sleep_by_delay_invalid(invalid_delay):
    """Test sleep_by_delay with invalid delay raises ValueError."""
    rate_limiter = RateLimiter()
    with pytest.raises(ValueError):
        rate_limiter.sleep_by_delay(invalid_delay)

def test_thread_safety():
    """Test thread safety of the RateLimiter."""
    rate_limiter = RateLimiter()
    delay = 0.1

    @rate_limiter.set_by_delay(delay)
    def func():
        return time.time()

    # Call the function from multiple threads
    results = []
    threads = []

    def worker():
        results.append(func())

    # Create and start threads
    for _ in range(5):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Sort the results by time
    results.sort()

    # Check that the time between calls is at least the expected delay
    for i in range(1, len(results)):
        assert results[i] - results[i-1] >= delay * 0.9  # Allow for small timing variations


def test_different_functions():
    """Test that different functions have independent rate limits."""
    rate_limiter = RateLimiter()
    delay = 0.1

    @rate_limiter.set_by_delay(delay)
    def func1():
        return time.time()

    @rate_limiter.set_by_delay(delay)
    def func2():
        return time.time()

    # Call func1, then immediately call func2
    time1 = func1()
    time2 = func2()

    # The time difference should be less than the delay since they're different functions
    assert time2 - time1 < delay


# pytest doesn't require a main block
