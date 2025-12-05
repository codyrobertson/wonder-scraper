from sqlmodel import Session, select
from app.db import engine
from app.models.market import MarketPrice
from app.models.card import Card
from app.scraper.ebay import _detect_treatment

def backfill_treatments():
    with Session(engine) as session:
        print("Fetching all market prices...")
        prices = session.exec(select(MarketPrice)).all()
        print(f"Found {len(prices)} prices to check.")

        # Build card_id -> product_type lookup
        cards = session.exec(select(Card)).all()
        card_product_types = {card.id: card.product_type for card in cards}

        updated_count = 0
        for price in prices:
            # Get product_type from card lookup (default to "Single" if not found)
            product_type = card_product_types.get(price.card_id, "Single")

            current_treatment = price.treatment
            detected_treatment = _detect_treatment(price.title, product_type)

            if current_treatment != detected_treatment:
                price.treatment = detected_treatment
                session.add(price)
                updated_count += 1

        session.commit()
        print(f"Successfully updated {updated_count} records with correct treatments.")

if __name__ == "__main__":
    backfill_treatments()

