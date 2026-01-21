import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "webScrapers"

def run(cmd, cwd=None):
    print("\n+", " ".join(map(str, cmd)), flush=True)
    subprocess.run(list(map(str, cmd)), check=True, cwd=str(cwd) if cwd else None)

def main():
    py = sys.executable



    # 1) NOS
    run([
        py, "webScrapers/scrape_nos_feeds.py",
        "--max_feeds", "10",
        "--max_items_per_feed", "5",
        "--out_json", "scrapedArticles/nos_articles.json",
    ], cwd=ROOT)

    # 2) BD
    run([py, "scrape_bd.py"], cwd=WEB)

    # 3) Gelderlander
    run([py, "scrape_gelderlander.py"], cwd=WEB)

    # 4) Politie (API update mode)
    run([py, "webScrapers/scrape_police.py", "--update"], cwd=ROOT)

    # 5) L1
    run([py, "scrape_l1.py"], cwd=WEB)

    # 6) Omroep West
    run([py, "scrape_omroep_west.py"], cwd=WEB)

    # 7) RTV Noord
    run([py, "scrape_rtv_noord.py"], cwd=WEB)

    # 8) Merge
    run([py, "merge_jsons.py"], cwd=ROOT)




    print("\ningestion finished")

if __name__ == "__main__":
    main()
