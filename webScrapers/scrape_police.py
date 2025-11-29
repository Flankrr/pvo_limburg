import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone

BASE_URL = "https://api.politie.nl/v4/nieuws"

# Date window for October 2025
FROM_DATE = "20251001"
TO_DATE = "20251031"

OUTPUT_FILE = f"police_{FROM_DATE}-{TO_DATE}.json"


def convert_article(old):
    # --- extract and clean full text ---
    paragraphs = []

    for alinea in old.get("alineas", []):
        html = alinea.get("opgemaaktetekst", "")
        text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
        if text:
            paragraphs.append(text)

    # one-line full text
    full_text = " ".join(paragraphs)

    # --- convert publish date to RFC1123 ---
    try:
        dt = datetime.strptime(old["publicatiedatum"], "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        published_rfc = dt.strftime("%a, %d %b %Y %H:%M:%S GMT")
    except Exception:
        published_rfc = old.get("publicatiedatum", "")

    # --- build new format ---
    new = {
        "feed": "Politie",
        "title": old.get("titel", ""),
        "url": old.get("url", ""),
        "published": published_rfc,
        "summary": old.get("introductie", ""),
        "full_text": full_text,
        "scraped_at": datetime.now(timezone.utc).isoformat()
    }

    return new



def fetch_news_october_2025():
    all_items = []
    offset = 0
    max_items = 25  # allowed values: 10 or 25

    while True:
        params = {
            "fromdate": FROM_DATE,
            "todate": TO_DATE,
            "language": "nl",
            "maxnumberofitems": max_items,
            "offset": offset
        }

        print(f"Requesting offset {offset}...")
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()

        data = response.json()

        # If no results
        if "nieuwsberichten" not in data or not data["nieuwsberichten"]:
            print("No more results found.")
            break

        # Accumulate items
        all_items.extend(data["nieuwsberichten"])

        # Check iterator to know if there's another page
        iterator = data.get("iterator", {})
        if iterator.get("last", True):
            break  # This was the last page

        # Otherwise request next page
        offset += max_items

    # Save results
    converted = [convert_article(item) for item in all_items]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=4)


    print(f"Saved {len(all_items)} items to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_news_october_2025()
