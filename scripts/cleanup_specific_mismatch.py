from sqlmodel import Session, select
from app.db import engine
from app.models.card import Card
from app.models.market import MarketPrice
from app.scraper.ebay import _is_valid_match, _clean_title_text

def cleanup_ethereal_mismatches():
    print("Cleaning up 'Ethereal Grove' mismatches...")
    with Session(engine) as session:
        # ID 95 is 'Ethereal Grove' (Epic)
        # ID 43 is 'Plant Terror of Ethereal Grove' (Mythic)
        
        # Problem: Listings for "Plant Terror of Ethereal Grove" are matching "Ethereal Grove"
        # because "Ethereal Grove" is a subset of the other name.
        
        card_eg = session.get(Card, 95)
        card_pt = session.get(Card, 43)
        
        if not card_eg or not card_pt:
            print("Cards not found.")
            return

        # Get all listings for Ethereal Grove
        listings_eg = session.exec(select(MarketPrice).where(MarketPrice.card_id == 95)).all()
        
        deleted_count = 0
        for listing in listings_eg:
            title_lower = listing.title.lower()
            
            # Explicit check: If title contains "Plant Terror", it belongs to ID 43, NOT 95.
            if "plant terror" in title_lower:
                print(f"Deleting Mismatch: Listing '{listing.title}' assigned to '{card_eg.name}' but contains 'Plant Terror'")
                session.delete(listing)
                deleted_count += 1
                
        session.commit()
        print(f"Deleted {deleted_count} bad listings for Ethereal Grove.")

if __name__ == "__main__":
    cleanup_ethereal_mismatches()

