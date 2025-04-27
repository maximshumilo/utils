# Shumilo Utils

A collection of utility modules for Python applications.

## Rate Limiter

A thread-safe utility for limiting the rate of function calls in Python applications.

### Installation

```bash
pip install shumilo-utils
```

### Features

- Limit function calls by requests per second (RPS) or minimum delay between calls
- Thread-safe implementation
- Can be used as a decorator or directly via sleep methods
- Supports different rate limits for different functions
- Lightweight with minimal dependencies

### Usage Examples

#### Basic Usage as a Decorator

```python
from shumilo_utils.rate_limiter import RateLimiter

# Create a rate limiter with default settings
rate_limiter = RateLimiter(rps=5)  # Limit to 5 requests per second

# Apply the rate limiter as a decorator
@rate_limiter
def my_function():
    print("Function called")

# Now my_function() will be limited to 5 calls per second
for _ in range(10):
    my_function()  # Will automatically sleep as needed to maintain the rate limit
```

#### Using with RPS Parameter

```python
from shumilo_utils.rate_limiter import RateLimiter

# Create a rate limiter
rate_limiter = RateLimiter()

# Apply the rate limiter with specific RPS
@rate_limiter.set_by_rps(10)  # Limit to 10 requests per second
def api_call():
    print("API called")

# Now api_call() will be limited to 10 calls per second
for _ in range(20):
    api_call()
```

#### Using with Delay Parameter

```python
from shumilo_utils.rate_limiter import RateLimiter

# Create a rate limiter
rate_limiter = RateLimiter()

# Apply the rate limiter with specific delay
@rate_limiter.set_by_delay(0.5)  # Minimum 0.5 seconds between calls
def database_query():
    print("Database queried")

# Now database_query() will have at least 0.5 seconds between calls
for _ in range(5):
    database_query()
```

#### Direct Usage with Sleep Methods

```python
import time
from shumilo_utils.rate_limiter import RateLimiter

# Create a rate limiter
rate_limiter = RateLimiter()

# Use the rate limiter directly in a loop
for i in range(10):
    # This will sleep as needed to maintain 2 iterations per second
    rate_limiter.sleep_by_rps(2)
    print(f"Iteration {i} at {time.time()}")

# Or use delay-based limiting
for i in range(10):
    # This will ensure at least 0.3 seconds between iterations
    rate_limiter.sleep_by_delay(0.3)
    print(f"Iteration {i} at {time.time()}")
```

### API Documentation

#### RateLimiter Class

```python
RateLimiter(rps=None, delay=None)
```

**Parameters:**
- `rps` (float, optional): Maximum requests per second. If provided, sets the default interval as 1/rps.
- `delay` (float, optional): Minimum delay between calls (in seconds). If provided, sets the default interval.

**Note:** You can specify either `rps` or `delay`, but not both.

#### Methods

##### `__call__(func)`
Use the RateLimiter as a decorator with default settings.

##### `set_by_rps(max_rps)`
Set to limit function calls based on maximum requests per second (RPS).

**Parameters:**
- `max_rps` (float): Maximum number of requests per second.

##### `set_by_delay(delay_sec)`
Set delay to limit function calls based on the minimum delay between calls.

**Parameters:**
- `delay_sec` (float): Minimum delay between consecutive calls (in seconds).

##### `sleep_by_rps(max_rps)`
Sleep the execution to maintain a maximum rate of requests per second.

**Parameters:**
- `max_rps` (float): Maximum number of requests per second allowed.

##### `sleep_by_delay(delay_sec)`
Sleep for a specific delay period.

**Parameters:**
- `delay_sec` (float): The delay period (in seconds) for which the program execution should be paused.

### Thread Safety

The RateLimiter is designed to be thread-safe. It uses locks to ensure that rate limiting works correctly even when the decorated functions are called from multiple threads simultaneously.

### Common Use Cases

- API rate limiting to avoid hitting service limits
- Database query throttling to prevent overloading the database
- Network request throttling to manage bandwidth
- Controlling the frequency of resource-intensive operations
- Implementing backoff strategies for retries

### Limitations

- The rate limiter uses `time.sleep()` which blocks the current thread. For non-blocking applications (e.g., async), a different approach would be needed.
- The rate limiter is per-process. If you have multiple processes, each will have its own independent rate limiter.

### License

MIT
