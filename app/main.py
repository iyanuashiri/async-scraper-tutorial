import sys

from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .schemas import ScrapeRequest
from .scraper import scrape_webpage
from .strategies import STRATEGIES
from .utils import break_string, fix_url

app = FastAPI(title="Async Scraper Tutorial")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.remove(0)
logger.add(sys.stderr, level="INFO")


@app.post("/scrape/", status_code=status.HTTP_200_OK)
async def scrape(request: ScrapeRequest, response: Response):
    """
    Scrapes job listing URLs from a Workday careers page, then processes
    each one with the concurrency strategy named in `request.strategy`.

    Send the same request with a different `strategy` value —
    "gather", "wait", "as_completed", "semaphore", or "queue" — to compare
    how each one behaves. The implementation for each lives in its own
    file under app/strategies/, matching the article section by section.
    """
    if request.strategy not in STRATEGIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown strategy '{request.strategy}'. Choose from: {list(STRATEGIES)}",
        )

    if "myworkdayjobs" not in request.url:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"error": "This is not a Workday careers page. Nothing to scrape."}

    company_name, wd = break_string(request.url)

    # Step 1: scrape the paginated careers homepage for job listing URLs.
    documents = await scrape_webpage(url=request.url, is_paginated=True)

    job_urls = []
    for document in documents:
        soup = BeautifulSoup(document, "html.parser")
        for anchor in soup.find_all("a", class_="css-19uc56f", href=True):
            job_urls.append(fix_url(anchor["href"], company_name, wd))

    if request.existing_urls:
        job_urls = list(set(job_urls) - set(request.existing_urls))

    if not job_urls:
        response.status_code = status.HTTP_204_NO_CONTENT
        return {"data": "No new job URLs to scrape."}

    # Step 2: process every job URL using the requested concurrency strategy.
    process_fn = STRATEGIES[request.strategy]
    jobs = await process_fn(job_urls)

    return {
        "strategy": request.strategy,
        "total_urls": len(job_urls),
        "jobs": jobs,
    }


@app.get("/")
async def root():
    return {
        "message": "POST /scrape/ with a Workday careers URL and a `strategy`.",
        "available_strategies": list(STRATEGIES),
    }
