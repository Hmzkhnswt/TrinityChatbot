import os
import json
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from TrinityBot.components.datascraping import SSRScraper

load_dotenv()

artifacts_dir = os.getenv("SCRAPPED_DATA_DIRECTORY", "artifacts/ScrappedData")
os.makedirs(artifacts_dir, exist_ok=True)

urls_to_scrape = {
    "trakx": "https://token.trakx.io/",
    "bidnow": "https://www.bidnow.my/"
}

scraper = SSRScraper(
    use_selenium=True,
    max_pages=5,
    concurrent_requests=3,
    chunk_size=1000,
    chunk_overlap=200
)

try:
    for token, url in urls_to_scrape.items():
        print(f"Starting scrape for URL: {url} (Token: {token})")
        
        documents = scraper.scrape_site(
            start_url=url,
            max_depth=1
        )
        
        filename = os.path.join(
            artifacts_dir,
            f"{token}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(filename, "w", encoding="utf-8") as file:
            json.dump([doc.dict() for doc in documents], file, ensure_ascii=False, indent=4)
        
        print(f"Scraped data saved to {filename}")
finally:
    scraper.cleanup()
