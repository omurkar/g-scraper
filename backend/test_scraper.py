"""
Standalone scraper test — run this to debug Google Maps scraping.
Usage: python test_scraper.py
"""
import asyncio
import sys
import os

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add backend to path  
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.scraper import scrape_google_maps


async def main():
    print("=" * 60)
    print("LeadScout Scraper Test — Dentists in Mumbai")
    print("=" * 60)

    leads = await scrape_google_maps(
        keyword="Dentists",
        location="Mumbai",
        max_results=10,
        on_progress=lambda d: print(f"  ✓ Got lead #{d['count']}: {d['lead']['business_name']}"),
    )

    print(f"\nTotal leads found: {len(leads)}")
    for i, lead in enumerate(leads, 1):
        print(f"\n[{i}] {lead['business_name']}")
        print(f"    Category: {lead.get('category', '—')}")
        print(f"    Rating:   {lead.get('rating', '—')} ★ ({lead.get('review_count', 0)} reviews)")
        print(f"    Phone:    {lead.get('phone', '—')}")
        print(f"    Address:  {lead.get('address', '—')}")
        print(f"    Website:  {lead.get('website_url', '—')}")
        print(f"    Maps URL: {lead.get('google_maps_url', '—')[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
