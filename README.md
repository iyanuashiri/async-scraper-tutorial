# async-scraper-tutorial

A small, runnable FastAPI service that scrapes Workday careers pages and
extracts structured job data with OpenAI — built as the companion code
for two articles:

1. **"Mastering asyncio: Building a Production Scraper from Scratch"**
   — `app/strategies/`, five ways to process a batch of URLs concurrently.
2. **"Rate Limiting in Python: From Sleep to Sliding Windows"**
   — `app/rate_limiting/`, three rate limiter implementations, replacing
   the `time.sleep(70)` this scraper originally shipped with.
3. **"4 Redis Patterns Every FastAPI Backend Eventually Needs"**
   — `app/redis_patterns/`, four independent, runnable patterns: caching,
   deduplication, distributed locks, and background job status.

## Structure

```
app/
├── main.py                     # FastAPI endpoint, dispatches by `strategy`
├── schemas.py                  # request + job data models
├── settings.py                 # env config
├── scraper.py                  # Playwright: fetch + paginate a page
├── utils.py                    # HTML stripping, URL helpers
├── extractor.py                # OpenAI call, rate-limited, with retries
├── strategies/
│   ├── gather_strategy.py         # asyncio.gather
│   ├── wait_strategy.py           # asyncio.wait (+ timeout)
│   ├── as_completed_strategy.py   # asyncio.as_completed
│   ├── semaphore_strategy.py      # asyncio.Semaphore
│   └── queue_strategy.py          # asyncio.Queue (producer/consumer)
└── rate_limiting/
    ├── sliding_window.py          # in-memory, single process (the default)
    ├── token_bucket.py            # in-memory, allows bursts
    └── redis_sliding_window.py    # shared across processes/containers

app/redis_patterns/
├── client.py            # shared Redis client
├── scrape_company.py    # shared "expensive work" helper (not Redis-specific)
├── caching.py            # Pattern 1: cache behind a TTL
├── dedup.py               # Pattern 2: track seen items with a Set
├── locking.py             # Pattern 3: one worker at a time, via SET NX PX
├── job_status.py          # Pattern 4: background jobs, status in a Hash
└── app.py                 # mounts all four as one demo app
```

Every strategy module exposes `async def process(urls: list[str]) -> list[dict]`,
so `main.py` doesn't need to know which one is running — pick one per
request via the `strategy` field and compare them directly.

Every rate limiter exposes `async def acquire() -> None`, so `extractor.py`
doesn't need to know which one is active either — by default it uses
`SlidingWindowRateLimiter`; swap in `RedisSlidingWindowRateLimiter` once
you're running more than one instance of this service (see below).

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # add your OpenAI API key
uvicorn app.main:app --reload
```

## Usage

```bash
curl -X POST http://localhost:8000/scrape/ \
  -H "Content-Type: application/json" \
  -d '{
        "url": "https://example.wd5.myworkdayjobs.com/en-US/careers",
        "strategy": "semaphore"
      }'
```

Swap `"strategy"` between `gather`, `wait`, `as_completed`, `semaphore`,
and `queue` to see each one run against the same URL set.

## Trying the distributed rate limiter

The default limiter in `extractor.py` is in-memory and only protects a
single process. To try the Redis-backed version instead:

```bash
docker compose up -d redis   # starts Redis on localhost:6379
```

Then in `extractor.py`, replace the `SlidingWindowRateLimiter` import and
instantiation with:

```python
from .rate_limiting.redis_sliding_window import build_redis_rate_limiter
from .settings import REDIS_URL

_rate_limiter = await build_redis_rate_limiter(
    REDIS_URL, key="openai-extract", max_requests=500, window_seconds=60.0
)
```

(`build_redis_rate_limiter` is async since it opens a connection — you'll
need to construct it once at startup, e.g. in a FastAPI lifespan handler,
rather than at import time like the in-memory version.)

## Trying the Redis patterns

```bash
docker compose up -d redis   # starts Redis on localhost:6379
uvicorn app.redis_patterns.app:app --reload --port 8001
```

Then try each pattern independently:

```bash
# Pattern 1: caching — second call for the same URL returns instantly
curl -X POST http://localhost:8001/scrape-cached/ -H "Content-Type: application/json" -d '{"url": "..."}'

# Pattern 2: dedup — only new job URLs get scraped on a repeat call
curl -X POST http://localhost:8001/scrape-dedup/ -H "Content-Type: application/json" -d '{"url": "..."}'

# Pattern 3: locking — fire this twice at once for the same URL; the
# second call gets a 409 instead of racing the first
curl -X POST http://localhost:8001/scrape-locked/ -H "Content-Type: application/json" -d '{"url": "..."}'

# Pattern 4: background jobs — returns a job_id immediately
curl -X POST http://localhost:8001/jobs/ -H "Content-Type: application/json" -d '{"url": "..."}'
curl http://localhost:8001/jobs/<job_id>
```

## What's intentionally left out

This is a teaching repo, not the production version:

- No S3 / cloud storage — results are returned directly as JSON.
- No proxy support — add your own if you're scraping at real volume.
- A 6-field extraction schema instead of a large taxonomy, so the
  prompt in `extractor.py` stays readable.
- The Redis limiter isn't wired in by default (to avoid requiring Redis
  just to run the demo) — see above for how to switch to it.

## License

MIT — use it, fork it, adapt it for your own scraper.
