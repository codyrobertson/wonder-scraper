import asyncio
import random
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.db import engine
from app.models.card import Card
from app.models.market import MarketSnapshot
from scripts.scrape_card import scrape_card
from app.scraper.browser import BrowserManager

async def bulk_scrape(limit: int = 1000, force_all: bool = False):
    """
    Scrapes a batch of cards.
    If force_all is True, it ignores the 24h check and scrapes everything.
    """
    print(f"Starting Bulk Scrape (Limit: {limit}, Force: {force_all})...")
    
    with Session(engine) as session:
        # Get all cards
        all_cards = session.exec(select(Card)).all()
        
        cards_to_scrape = []
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for card in all_cards:
            if force_all:
                cards_to_scrape.append(card)
            else:
                # Check latest snapshot
                snapshot = session.exec(
                    select(MarketSnapshot)
                    .where(MarketSnapshot.card_id == card.id)
                    .order_by(MarketSnapshot.timestamp.desc())
                    .limit(1)
                ).first()
                
                if not snapshot or snapshot.timestamp < cutoff_time:
                    cards_to_scrape.append(card)
                
            if len(cards_to_scrape) >= limit:
                break
                
    print(f"Found {len(cards_to_scrape)} cards needing update (out of {len(all_cards)} total).")
    
    if not cards_to_scrape:
        print("No cards need updating.")
        return

    # Initialize browser once
    await BrowserManager.get_browser()
    
    try:
        for i, card in enumerate(cards_to_scrape):
            # Simplified search term to catch more results. 
            # Many listings don't include "Existence" or "Set 1".
            # "Wonders of the First" is appended automatically by utils if needed, but let's be explicit.
            search_term = f"{card.name} Wonders of the First"
            print(f"\n[{i+1}/{len(cards_to_scrape)}] Processing: {card.name}")
            
            try:
                # Pass card_name separately from search_term to ensure strict validation
                await scrape_card(card_name=card.name, card_id=card.id, search_term=search_term)
            except Exception as e:
                print(f"Error scraping {card.name}: {e}")
            
            # Random delay to be polite/safe
            delay = random.uniform(2, 5)
            print(f"Sleeping for {delay:.2f}s...")
            await asyncio.sleep(delay)
            
    finally:
        await BrowserManager.close()
        print("Bulk Scrape Complete.")

if __name__ == "__main__":
    # Set force_all=True to ensure we update historical data for everything
    asyncio.run(bulk_scrape(limit=1000, force_all=True))
