import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
import time


BASE_URL = "https://api.politie.nl/v4/nieuws"

# Date window for October 2025
FROM_DATE = "20251001"
TO_DATE = "20251031"

OUTPUT_FILE = "scrapedArticles/politie.json"


def convert_article(old):
    # --- extract and clean full text ---
    paragraphs = []

    try:
        for alinea in old.get("alineas", []):
            html = alinea.get("opgemaaktetekst", "")
            text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
            if text:
                paragraphs.append(text)
    except:
        paragraphs.append("")

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



def fetch_news(from_date, to_date):
    all_items = []

    start_date = datetime.strptime(from_date, "%Y%m%d")
    end_date = datetime.strptime(to_date, "%Y%m%d")
    increment = timedelta(days=15)

    current_end = end_date

    while current_end >= start_date:
        current_start = max(current_end - increment + timedelta(days=1), start_date)
        offset = 0
        max_items = 25

        while True:
            params = {
                "fromdate": current_start.strftime("%Y%m%d"),
                "todate": current_end.strftime("%Y%m%d"),
                "language": "nl",
                "maxnumberofitems": max_items,
                "offset": offset
            }

            print(f"Requesting {params['fromdate']} to {params['todate']}, offset {offset}...")
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            # Correct key name
            if "nieuwsberichten" not in data or not data["nieuwsberichten"]:
                break

            all_items.extend(data["nieuwsberichten"])

            iterator = data.get("iterator", {})
            if iterator.get("last", True):
                break

            offset += max_items

        time.sleep(1)
        current_end = current_start - timedelta(days=1)

    converted = [convert_article(item) for item in all_items]
    return converted


def scrape_1yr():
    today = datetime.today().strftime("%Y%m%d")
    one_year_before = datetime.today().replace(year=datetime.today().year - 1).strftime("%Y%m%d")
    # one_year_before = "20251015"
    result = fetch_news(one_year_before, today)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)


def merge_and_dedupe(items, key="url"):
    seen = set()
    merged = []

    for item in items:
        identifier = item.get(key)
        if identifier not in seen:
            seen.add(identifier)
            merged.append(item)

    return merged

def update_csvs():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    published_str = data[0]["published"]
    dt = datetime.strptime(published_str, "%a, %d %b %Y %H:%M:%S %Z")

    update = dt.strftime("%Y%m%d")
    today = datetime.today().strftime("%Y%m%d")

    result = fetch_news(update, today)   

    merged = merge_and_dedupe(result + data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)


def buh_bye():
    print("Bye.")
    exit(0)

def main():
    while True:
        print("\n=== Main Menu ===")
        print("1) Scrape 1 year")
        print("2) Update")
        print("3) Exit")

        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            scrape_1yr()
        elif choice == "2":
            update_csvs()
        elif choice == "3":
            buh_bye()
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")



if __name__ == "__main__":
    # fetch_news(FROM_DATE, TO_DATE)
    main()
