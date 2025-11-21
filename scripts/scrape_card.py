import asyncio
import sys
from typing import Optional
from sqlmodel import Session, select
from app.db import engine
from app.models.card import Card, Rarity
from app.models.market import MarketSnapshot, MarketPrice
from app.scraper.browser import get_page_content
from app.scraper.utils import build_ebay_url
from app.scraper.ebay import parse_search_results, parse_total_results
from app.services.math import calculate_stats
from app.scraper.browser import BrowserManager
from app.scraper.active import scrape_active_data

async def scrape_card(card_name: str, card_id: int = 0, rarity_name: str = "", search_term: Optional[str] = None):
    # If no search_term provided, default to card_name
    query = search_term if search_term else card_name
    print(f"--- Scraping: {card_name} (Query: {query}) (Rarity: {rarity_name}) ---")
    
    # 1. Active Data
    print("Fetching active listings...")
    # Pass strict card_name for validation, but query for searching
    active_ask, active_inv, highest_bid = await scrape_active_data(card_name, card_id, search_term=query)
    
    # 2. Build URL for SOLD listings
    url = build_ebay_url(query, sold_only=True)
    print(f"Sold URL: {url}")
    
    # 2. Fetch HTML
    try:
        html = await get_page_content(url)
    except Exception as e:
        print(f"Failed to fetch: {e}")
        return

    # 3. Parse
    # Clean name for validation only
    clean_name = card_name.replace("Wonders of the First", "").strip()
    
    # Pass pure clean_name for validation
    prices = parse_search_results(html, card_id=card_id, card_name=clean_name, target_rarity=rarity_name)
    print(f"Found {len(prices)} sold listings.")
    
    # 4. Calculate Stats
    # Parse total volume from the page header if possible for accuracy
    total_volume = parse_total_results(html)
    # If parse_total_results returns 0 or fails, fallback to list length
    if prices:
        if total_volume <= 0:
            total_volume = len(prices)
        else:
            total_volume = max(total_volume, len(prices))
    
    if not prices:
        print("No sold data found.")
        stats = {"min": 0.0, "max": 0.0, "avg": 0.0, "volume": 0}
    else:
        price_values = [p.price for p in prices]
        stats = calculate_stats(price_values)
        # Override volume with the parsed total from header
        stats["volume"] = total_volume
        print(f"Stats: {stats} (Total Vol from Header: {total_volume})")
    
    # 5. Save to DB
    if card_id > 0:
        with Session(engine) as session:
            if prices:
                session.add_all(prices)
            
            snapshot = MarketSnapshot(
                card_id=card_id,
                min_price=stats["min"],
                max_price=stats["max"],
                avg_price=stats["avg"],
                volume=stats["volume"],
                lowest_ask=active_ask,
                highest_bid=highest_bid,
                inventory=active_inv
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            print(f"Saved Snapshot ID: {snapshot.id}")

async def main():
    # 1. Get a card from DB
    with Session(engine) as session:
        # Try to find 'Aerius of Thalwind'
        statement = select(Card).where(Card.name == "Aerius of Thalwind")
        card = session.exec(statement).first()
        
        if not card:
            print("Card not found in DB. Using dummy ID.")
            card_name = "Aerius of Thalwind"
            card_id = 0
            rarity_name = ""
            search_term = "Aerius of Thalwind"
        else:
            card_name = card.name
            search_term = f"{card.name} {card.set_name}"
            card_id = card.id
            rarity = session.get(Rarity, card.rarity_id)
            rarity_name = rarity.name if rarity else ""
            
    await scrape_card(card_name, card_id, rarity_name, search_term=search_term)
    
    # Close browser
    await BrowserManager.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        asyncio.run(scrape_card(sys.argv[1]))
    else:
        asyncio.run(main())
