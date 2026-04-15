import requests
from bs4 import BeautifulSoup
import time
import random

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

BASE_URL = "https://www.99acres.com/search/property/buy/residential-land/"

def fetch_page(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        return res.text
    except Exception as e:
        print("Error:", e)
        return None


def parse_listings(html):
    soup = BeautifulSoup(html, "html.parser")

    properties = []

    cards = soup.find_all("div", class_="srpTuple__tuple")

    for card in cards:
        try:
            title = card.find("h2").text.strip()

            price_tag = card.find("div", class_="srpTuple__price")
            price = price_tag.text.strip() if price_tag else "N/A"

            location_tag = card.find("div", class_="srpTuple__location")
            location = location_tag.text.strip() if location_tag else "N/A"

            properties.append({
                "title": title,
                "price": price,
                "location": location
            })

        except Exception:
            continue

    return properties


def scrape_99acres(pages=2):
    all_data = []

    for page in range(1, pages + 1):
        url = f"{BASE_URL}page-{page}"

        print(f"Scraping page {page}...")

        html = fetch_page(url)
        if html:
            data = parse_listings(html)
            all_data.extend(data)

        time.sleep(random.uniform(2, 5))  # avoid blocking

    return all_data


if __name__ == "__main__":
    data = scrape_99acres(2)
    print(f"Scraped {len(data)} properties")

    for d in data[:5]:
        print(d)