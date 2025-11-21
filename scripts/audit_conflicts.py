from sqlmodel import Session, select
from app.db import engine
from app.models.card import Card
from app.models.market import MarketPrice
from typing import List, Set, Tuple

STOPWORDS = {"the", "of", "a", "an", "in", "on", "at", "for", "to", "with", "by", "and", "or", "wonders", "first", "existence"}

def get_tokens(text: str) -> Set[str]:
    if not text: return set()
    return {t.lower() for t in text.split() if t.lower() not in STOPWORDS}

def audit_conflicts():
    print("Starting Conflict Audit...")
    with Session(engine) as session:
        cards = session.exec(select(Card)).all()
        print(f"Analyzing {len(cards)} cards for naming conflicts...")

        # 1. Identify Risk Pairs
        risk_pairs = []
        for i, card_a in enumerate(cards):
            tokens_a = get_tokens(card_a.name)
            if not tokens_a: continue

            for card_b in cards[i+1:]:
                tokens_b = get_tokens(card_b.name)
                if not tokens_b: continue

                # Check overlap
                intersection = tokens_a.intersection(tokens_b)
                
                # Risk Criteria 1: High Token Overlap (e.g. "The Great Usurper" vs "The Great Veridan")
                # If they share significant tokens but differ by only 1 or 2
                if len(intersection) >= 1:
                    # Calculate Jaccard similarity or simple overlap ratio
                    union = tokens_a.union(tokens_b)
                    ratio = len(intersection) / len(union)
                    
                    # If ratio is high, or if one is a subset of the other
                    is_subset = tokens_a.issubset(tokens_b) or tokens_b.issubset(tokens_a)
                    
                    if ratio > 0.5 or is_subset:
                         risk_pairs.append((card_a, card_b, list(intersection)))

        print(f"Found {len(risk_pairs)} pairs of cards with similar names.")

        # 2. Check DB for cross-contamination in these pairs
        mismatch_count = 0
        
        for card_a, card_b, shared in risk_pairs:
            # Identify unique tokens for each
            tokens_a = get_tokens(card_a.name)
            tokens_b = get_tokens(card_b.name)
            
            unique_a = tokens_a - tokens_b
            unique_b = tokens_b - tokens_a
            
            if not unique_a and not unique_b:
                continue

            # Check Listings for Card A that contain Unique tokens of Card B
            if unique_b:
                # We look for listings assigned to Card A
                listings_a = session.exec(select(MarketPrice).where(MarketPrice.card_id == card_a.id)).all()
                for listing in listings_a:
                    title_lower = listing.title.lower()
                    # Check if ALL unique tokens of B are in the title
                    # (Simple heuristic: if unique B word is in A's listing, it's suspicious)
                    for token in unique_b:
                        if token in title_lower.split(): # Exact word match
                            print(f"  [MISMATCH FOUND] Card A: '{card_a.name}' (ID: {card_a.id}) has listing '{listing.title}' containing B's unique token '{token}' (from '{card_b.name}')")
                            mismatch_count += 1
                            break # Count listing once

            # Check Listings for Card B that contain Unique tokens of Card A
            if unique_a:
                listings_b = session.exec(select(MarketPrice).where(MarketPrice.card_id == card_b.id)).all()
                for listing in listings_b:
                    title_lower = listing.title.lower()
                    for token in unique_a:
                        if token in title_lower.split():
                            print(f"  [MISMATCH FOUND] Card B: '{card_b.name}' (ID: {card_b.id}) has listing '{listing.title}' containing A's unique token '{token}' (from '{card_a.name}')")
                            mismatch_count += 1
                            break

        if mismatch_count == 0:
            print("\nAudit Complete: No obvious cross-contamination found in Risk Pairs.")
        else:
            print(f"\nAudit Complete: Found {mismatch_count} potential mismatches.")

if __name__ == "__main__":
    audit_conflicts()
