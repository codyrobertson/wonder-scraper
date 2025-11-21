"""
Distributed backfill script using multiprocessing for parallel scraping.
"""
import asyncio
import multiprocessing as mp
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.db import engine
from app.models.card import Card
from app.models.market import MarketSnapshot
from scripts.scrape_card import scrape_card
from app.scraper.browser import BrowserManager
import sys

async def scrape_card_worker(card_data: dict):
    """Worker function to scrape a single card."""
    try:
        print(f"[Worker {mp.current_process().name}] Processing: {card_data['name']}")
        await scrape_card(
            card_name=card_data['name'],
            card_id=card_data['id'],
            search_term=card_data['search_term'],
            set_name=card_data['set_name'],
            product_type=card_data['product_type']
        )
        print(f"[Worker {mp.current_process().name}] Completed: {card_data['name']}")
        return True
    except Exception as e:
        print(f"[Worker {mp.current_process().name}] Error on {card_data['name']}: {e}")
        return False
    finally:
        # Clean up browser for this worker
        try:
            await BrowserManager.close()
        except:
            pass

def worker_process(card_data: dict):
    """Wrapper to run async scrape in a process."""
    return asyncio.run(scrape_card_worker(card_data))

async def distributed_backfill(num_workers: int = 4, force_all: bool = False, limit: int = 1000):
    """
    Distributed backfill using multiprocessing.
    
    Args:
        num_workers: Number of parallel worker processes
        force_all: If True, scrape all cards regardless of age
        limit: Maximum cards to process
    """
    print(f"Starting Distributed Backfill with {num_workers} workers...")
    print(f"Force all: {force_all}, Limit: {limit}")
    
    # Fetch cards that need scraping
    with Session(engine) as session:
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
    
    if not cards_to_scrape:
        print("No cards need updating.")
        return
    
    print(f"Found {len(cards_to_scrape)} cards to scrape.")
    
    # Prepare card data for workers
    card_data_list = [
        {
            'id': card.id,
            'name': card.name,
            'set_name': card.set_name,
            'search_term': f"{card.name} {card.set_name}",
            'product_type': card.product_type if hasattr(card, 'product_type') else 'Single'
        }
        for card in cards_to_scrape
    ]
    
    # Distribute work across processes
    print(f"Distributing {len(card_data_list)} cards across {num_workers} workers...")
    
    with mp.Pool(processes=num_workers) as pool:
        results = pool.map(worker_process, card_data_list)
    
    success_count = sum(1 for r in results if r)
    print(f"\n=== Backfill Complete ===")
    print(f"Total: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")

if __name__ == "__main__":
    # Parse command line args
    num_workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    force_all = '--force' in sys.argv
    limit = 1000
    
    # Set multiprocessing start method
    mp.set_start_method('spawn', force=True)
    
    asyncio.run(distributed_backfill(num_workers=num_workers, force_all=force_all, limit=limit))

