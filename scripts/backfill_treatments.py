from sqlmodel import Session, select
from app.db import engine
from app.models.market import MarketPrice
from app.scraper.ebay import _detect_treatment

def backfill_treatments():
    with Session(engine) as session:
        print("Fetching all market prices...")
        prices = session.exec(select(MarketPrice)).all()
        print(f"Found {len(prices)} prices to check.")
        
        updated_count = 0
        for price in prices:
            current_treatment = price.treatment
            detected_treatment = _detect_treatment(price.title)
            
            if current_treatment != detected_treatment:
                price.treatment = detected_treatment
                session.add(price)
                updated_count += 1
        
        session.commit()
        print(f"Successfully updated {updated_count} records with correct treatments.")

if __name__ == "__main__":
    backfill_treatments()

