"""Quick test: does the sync-thread scraper work from asyncio.run()?"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

from services.scraper import scrape_google_maps

async def main():
    print("Starting scrape test (3 results)...")
    results = await scrape_google_maps("Restaurant", "Mumbai", max_results=3)
    print(f"\n=== GOT {len(results)} results ===")
    for r in results:
        print(f"  - {r['business_name']}  |  {r.get('phone', '')}  |  {r.get('website_url', '')}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
