# Treatment-Aware Pricing System

## Problem Statement

TCG cards come in different treatments/finishes (Classic Paper, Foil, Stonefoil, Serialized, etc.). When calculating average prices, mixing all treatments creates misleading data:

**Example: "Emma Shockbite"**
- Classic Paper: $5 (80 sales)
- Classic Foil: $15 (15 sales)
- Stonefoil: $150 (5 sales)
- **Mixed VWAP**: ~$20 (misleading!)
- **What users actually pay**: $5 for paper

High-end variants skew the average, making it harder for buyers to know what they'll actually pay.

---

## Solution: Two-Tier Pricing

### Option 1: Base Treatment Filtering (✅ Implemented)

**What it does:**
- Separates pricing into "base" and "premium" treatments
- Shows realistic floor price (what most people pay)
- Tracks premium variants separately

**New API Fields:**

```typescript
{
  vwap: 20.00,           // Average of ALL treatments (existing)
  base_price: 6.50,      // Average of Classic Paper + Classic Foil only
  premium_high: 150.00,  // Highest premium variant sale (Stonefoil, OCM, etc.)
  base_volume: 95,       // Number of base treatment sales
  premium_volume: 5      // Number of premium treatment sales
}
```

**Base Treatments:**
- Classic Paper
- Classic Foil

**Premium Treatments:**
- Stonefoil
- Formless Foil
- OCM Serialized
- Prerelease
- Promo
- Proof/Sample
- Error/Errata

### Option 2: Treatment-Specific Tracking (🔧 Foundation Ready)

**What it enables:**
- Separate MarketSnapshot per treatment
- Track price trends for each variant independently
- Support collectors who want specific treatments

**Database Schema:**

```python
class MarketSnapshot(SQLModel, table=True):
    card_id: int
    treatment: str  # 'All', 'Classic Paper', 'Stonefoil', etc.
    avg_price: float
    volume: int
    # ... other fields
```

**Future Queries:**
```sql
-- Get Classic Paper pricing
SELECT * FROM marketsnapshot
WHERE card_id = 123 AND treatment = 'Classic Paper'

-- Get Stonefoil pricing
SELECT * FROM marketsnapshot
WHERE card_id = 123 AND treatment = 'Stonefoil'
```

---

## Usage

### API Response

```bash
GET /cards?limit=50&time_period=24h
```

**Response:**
```json
{
  "id": 42,
  "name": "Emma Shockbite",
  "vwap": 20.00,
  "base_price": 6.50,
  "premium_high": 150.00,
  "base_volume": 95,
  "premium_volume": 5,
  "last_sale_treatment": "Classic Paper"
}
```

### Running the Migration

To add treatment tracking to existing snapshots:

```bash
poetry run python scripts/migrate_treatment_tracking.py
```

This adds the `treatment` column to `marketsnapshot` table with default value `'All'`.

---

## Implementation Details

### Detection Logic

Treatment is detected from eBay listing titles using keyword matching:

```python
# app/scraper/ebay.py:56-87

def _detect_treatment(title: str) -> str:
    title_lower = title.lower()

    # Serialized (highest priority)
    if "serialized" in title_lower or "/10" in title_lower:
        return "OCM Serialized"

    # Special Foils
    if "stonefoil" in title_lower:
        return "Stonefoil"

    # Classic Foil
    if "foil" in title_lower:
        return "Classic Foil"

    # Default
    return "Classic Paper"
```

### Price Calculation

Base price filtering (Classic Paper/Foil only):

```sql
-- app/api/cards.py:157-168
SELECT card_id, AVG(price) as base_price, COUNT(*) as volume
FROM marketprice
WHERE card_id IN (...)
AND listing_type = 'sold'
AND treatment IN ('Classic Paper', 'Classic Foil')
GROUP BY card_id
```

Premium high (max premium variant):

```sql
-- app/api/cards.py:172-183
SELECT card_id, MAX(price) as premium_high, COUNT(*) as volume
FROM marketprice
WHERE card_id IN (...)
AND listing_type = 'sold'
AND treatment NOT IN ('Classic Paper', 'Classic Foil')
GROUP BY card_id
```

---

## Future Enhancements

### Phase 1: Frontend Display (Next)
- Show base_price as primary price
- Display premium_high as a separate "Premium Variants" section
- Add tooltips explaining treatment types

### Phase 2: Per-Treatment Snapshots
- Modify scraper to create separate snapshots per treatment
- Update `scripts/scrape_card.py` to group sales by treatment
- Create one snapshot per treatment per scrape

### Phase 3: Treatment Filter UI
- Add treatment selector in frontend
- Allow users to view pricing for specific treatments
- Chart price trends per treatment

---

## Benefits

✅ **Accurate floor pricing** - Users see what they'll actually pay
✅ **Premium tracking** - Collectors can find high-end variants
✅ **Volume context** - Know if prices are based on 5 or 500 sales
✅ **Future-proof** - Foundation for per-treatment snapshots
✅ **Backwards compatible** - Existing VWAP still available

---

## Testing

1. Check base_price reflects common variants:
```bash
curl http://localhost:8000/cards/42 | jq '.base_price'
```

2. Verify premium_high shows max variant:
```bash
curl http://localhost:8000/cards/42 | jq '.premium_high'
```

3. Compare volumes:
```bash
curl http://localhost:8000/cards/42 | jq '{base_volume, premium_volume}'
```

---

## Rollback

If needed, revert the migration:

```sql
ALTER TABLE marketsnapshot DROP COLUMN treatment;
```

The API will still work - it just won't populate treatment-specific fields.
