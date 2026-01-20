#!/usr/bin/env python3
"""
scrape_gelderlander.py
Scrapes De Gelderlander Economie RSS feed and appends to all_articles.json (no duplicates)

Usage:
  python scrape_gelderlander.py
"""

import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any
import sys
import requests
import feedparser
from bs4 import BeautifulSoup
from pathlib import Path

try:
    from readability import Document
except ImportError:
    Document = None

# Configuration
FEED_URL = "https://www.gelderlander.nl/economie/rss.xml"
FEED_NAME = "De Gelderlander - Economie"
OUTPUT_FILE = "../scrapedArticles/gelderlander.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PVO-Limburg/1.0)"}
REQ_TIMEOUT = 12
REQUEST_SLEEP = 0.3
MAX_ITEMS = 30  # Default max items to scrape


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clean_whitespace(s: str) -> str:
    return " ".join(s.split()) if s else ""


def extract_main_text(html: str) -> str:
    """Extract main article text using readability -> fallback to <p> tags."""
    if not html:
        return ""
    text = ""
    try:
        if Document is not None:
            doc = Document(html)
            soup = BeautifulSoup(doc.summary(), "html.parser")
            text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        else:
            soup = BeautifulSoup(html, "html.parser")
            text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
    except Exception:
        pass
    return clean_whitespace(text)


def fetch_article(url: str) -> str:
    """Download article HTML and extract text."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQ_TIMEOUT)
        if resp.status_code == 200:
            return extract_main_text(resp.text)
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
    return ""


def load_existing_articles() -> tuple[List[Dict[str, Any]], set]:
    """Load existing articles from all_articles.json and return list + URL set"""
    if not Path(OUTPUT_FILE).exists():
        print(f"[INFO] {OUTPUT_FILE} doesn't exist yet, will create new file")
        return [], set()
    
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            articles = json.load(f)
            urls = {article.get('url') for article in articles if article.get('url')}
            print(f"[INFO] Loaded {len(articles)} existing articles")
            return articles, urls
    except Exception as e:
        print(f"[WARN] Error loading {OUTPUT_FILE}: {e}")
        return [], set()


def scrape_feed(max_items: int = MAX_ITEMS) -> List[Dict[str, Any]]:
    print(f"📡 Fetching feed: {FEED_NAME}")
    print(f"   URL: {FEED_URL}\n")
    
    feed = feedparser.parse(FEED_URL)
    entries = feed.entries[:max_items]
    results = []

    for entry in entries:
        url = entry.get("link", "")
        title = clean_whitespace(entry.get("title", ""))
        summary = clean_whitespace(entry.get("summary", ""))
        published = entry.get("published", "")
        
        print(f"📰 Scraping: {title[:80]}...")
        full_text = fetch_article(url)
        
        results.append({
            "feed": FEED_NAME,
            "title": title,
            "url": url,
            "published": published,
            "summary": summary,
            "full_text": full_text,
            "scraped_at": now_utc_iso(),
        })
        time.sleep(REQUEST_SLEEP)
    
    return results


def save_articles(new_articles: List[Dict[str, Any]]):
    """Append new articles to all_articles.json (skip duplicates)"""
    
    # Load existing articles
    all_articles, existing_urls = load_existing_articles()
    
    # Filter out duplicates
    added_count = 0
    for article in new_articles:
        if article.get('url') not in existing_urls:
            all_articles.append(article)
            existing_urls.add(article.get('url'))
            added_count += 1
        else:
            print(f"[SKIP] Duplicate: {article.get('title', '')[:50]}...")
    
    # Save back to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Added {added_count} new articles (skipped {len(new_articles) - added_count} duplicates)")
    print(f"📊 Total articles in {OUTPUT_FILE}: {len(all_articles)}")


if __name__ == "__main__":
    print("=" * 60)
    print("De Gelderlander - Economie Scraper")
    print("=" * 60 + "\n")
    
    articles = scrape_feed()
    print(f"\n✅ Scraped {len(articles)} articles from {FEED_NAME}")
    
    save_articles(articles)
    
    print("\n" + "=" * 60)
    print("Scraping complete!")
    print("=" * 60)