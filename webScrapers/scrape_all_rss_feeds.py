#!/usr/bin/env python3
"""
scrape_all_rss_feeds.py
A unified RSS feed scraper for PVO Limburg that supports multiple sources.
"""

import argparse
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

import requests
import feedparser
from bs4 import BeautifulSoup

try:
    from readability import Document
except ImportError:
    Document = None

# Configuration
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PVO-Limburg/1.0)"}
REQ_TIMEOUT = 12
REQUEST_SLEEP = 0.3

# Default feed sources
DEFAULT_SOURCES = {
    "limburger_economie": {
        "name": "De Limburger - Economie",
        "url": "https://www.limburger.nl/extra/rssfeed/22594085.html",
        "enabled": True
    },
    "ncsc": {
        "name": "Nationaal Cyber Security Centrum - Nieuwsberichten",
        "url": "https://www.ncsc.nl/actueel/nieuws.rss",
        "enabled": True
    },
    "nos": {
        "name": "NOS Nieuws",
        "url": "https://feeds.nos.nl/nosnieuwsalgemeen",
        "enabled": True
    },
    "security_nl": {
        "name": "Security.nl",
        "url": "https://www.security.nl/rss/headlines.xml",
        "enabled": True
    }
}


def now_utc_iso() -> str:
    """Return current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clean_whitespace(s: str) -> str:
    """Clean up excessive whitespace in text."""
    return " ".join(s.split()) if s else ""


def extract_main_text(html: str) -> str:
    """Extract main article text using readability, with fallback to <p> tags."""
    if not html:
        return ""
    
    text = ""
    
    # Try Readability first
    if Document is not None:
        try:
            doc = Document(html)
            soup = BeautifulSoup(doc.summary(), "html.parser")
            text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
            if text and len(text.split()) > 40:
                return clean_whitespace(text)
        except Exception:
            pass
    
    # Fallback: collect all <p> text
    try:
        soup = BeautifulSoup(html, "html.parser")
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
    except Exception:
        pass
    
    return clean_whitespace(text)


def fetch_article(url: str) -> str:
    """Download article HTML and extract text."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQ_TIMEOUT)
        resp.raise_for_status()
        return extract_main_text(resp.text)
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}", file=sys.stderr)
    return ""


def scrape_feed(feed_name: str, feed_url: str, max_items: int = 0) -> List[Dict[str, Any]]:
    """Scrape a single RSS/Atom feed."""
    print(f"📡 Fetching feed: {feed_name}", file=sys.stderr)
    
    try:
        feed = feedparser.parse(feed_url)
        
        # Check if feed was parsed successfully
        if hasattr(feed, 'bozo') and feed.bozo:
            print(f"[WARN] Feed parsing warning for {feed_name}: {getattr(feed, 'bozo_exception', 'Unknown error')}", file=sys.stderr)
        
        entries = feed.entries
        if max_items > 0:
            entries = entries[:max_items]
        
        if not entries:
            print(f"[WARN] No entries found in feed: {feed_name}", file=sys.stderr)
            return []
        
        results = []
        seen_urls = set()
        
        for entry in entries:
            url = entry.get("link") or entry.get("id") or ""
            
            # Skip duplicates
            if url in seen_urls or not url:
                continue
            seen_urls.add(url)
            
            title = clean_whitespace(entry.get("title", ""))
            summary = entry.get("summary") or entry.get("description") or ""
            published = entry.get("published") or entry.get("updated") or ""
            
            print(f"📰 Scraping: {title[:80]}...", file=sys.stderr)
            
            # Fetch full article text
            full_text = fetch_article(url)
            
            results.append({
                "feed": feed_name,
                "title": title,
                "url": url,
                "published": published,
                "summary": summary,
                "full_text": full_text,
                "scraped_at": now_utc_iso(),
            })
            
            time.sleep(REQUEST_SLEEP)
        
        print(f"✅ Scraped {len(results)} articles from {feed_name}", file=sys.stderr)
        return results
        
    except Exception as e:
        print(f"[ERROR] Failed to scrape {feed_name}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return []


def load_sources_config(config_path: Optional[str] = "sources.json") -> Dict[str, Dict[str, Any]]:
    """Load sources configuration from JSON file or use defaults."""
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load config from {config_path}: {e}", file=sys.stderr)
            print("[INFO] Using default sources", file=sys.stderr)
    
    return DEFAULT_SOURCES


def save_json(data: List[Dict[str, Any]], out_path: str, pretty: bool = False):
    """Save articles to JSON file."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            json.dump(data, f, ensure_ascii=False)
    
    print(f"✅ Saved {len(data)} articles to {out_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Unified RSS feed scraper for PVO Limburg")
    
    parser.add_argument("--config", help="Path to JSON configuration file with feed sources")
    parser.add_argument("--source", help="Scrape only a specific source")
    parser.add_argument("--out", help="Output JSON file path")
    parser.add_argument("--max-items", type=int, default=0, help="Maximum items per feed (0 = all)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--list-sources", action="store_true", help="List available sources and exit")
    
    args = parser.parse_args()
    
    # Load sources configuration
    config_path = args.config if args.config else "sources.json"
    sources = load_sources_config(args.config)
    
    # List sources if requested
    if args.list_sources:
        print("\n📋 Available sources:", file=sys.stderr)
        for key, config in sources.items():
            status = "✓" if config.get("enabled", True) else "✗"
            print(f"  {status} {key}: {config['name']}", file=sys.stderr)
            print(f"     URL: {config['url']}", file=sys.stderr)
        return
    
    # --out is required if not listing sources
    if not args.out:
        parser.error("the following arguments are required: --out")
    
    # Filter sources
    if args.source:
        if args.source not in sources:
            print(f"[ERROR] Source '{args.source}' not found in configuration", file=sys.stderr)
            print(f"[INFO] Available sources: {', '.join(sources.keys())}", file=sys.stderr)
            sys.exit(1)
        sources = {args.source: sources[args.source]}
    else:
        # Only use enabled sources
        sources = {k: v for k, v in sources.items() if v.get("enabled", True)}
    
    # Scrape all sources
    all_articles = []
    for source_key, config in sources.items():
        articles = scrape_feed(
            feed_name=config["name"],
            feed_url=config["url"],
            max_items=args.max_items
        )
        all_articles.extend(articles)
    
    # Save results
    save_json(all_articles, args.out, pretty=args.pretty)
    
    print(f"\n🎉 Successfully scraped {len(all_articles)} articles from {len(sources)} source(s)", file=sys.stderr)


if __name__ == "__main__":
    main()