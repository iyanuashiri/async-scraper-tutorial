import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    # Not raising here — lets you import the app (and read the code) without
    # a key set. You'll only hit an error once a request actually calls
    # the OpenAI API in app/extractor.py.
    pass

# Used by the optional Redis-backed rate limiter in
# app/rate_limiting/redis_sliding_window.py, and by every pattern under
# app/redis_patterns/.
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
