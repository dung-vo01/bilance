import os

# Tests must never touch a real Redis: limiter.reset() would wipe its counters.
os.environ["RATE_LIMIT_STORAGE_URI"] = "memory://"
