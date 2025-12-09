# EPIC-7: ETL & Data Ingestion

**Status**: Planned
**Sprint**: 4-5
**Priority**: High
**Dependencies**: EPIC-6 (API Layer)

---

## Objective

Build data ingestion pipelines for CSV imports, ShootStrayt scraping, and update existing scrapers to create Seller records.

## User Impact

Automated seller/inventory tracking without manual data entry.

## Tech Scope

- CSV parser with validation
- ShootStrayt scraper (SKU parsing)
- eBay/Blokpax scraper updates
- Background jobs for snapshots

---

## Done-When Criteria

- [ ] CSV import processes 1000-row file in <30 seconds
- [ ] ShootStrayt scraper fetches inventory successfully
- [ ] eBay scraper creates Seller records for new sellers
- [ ] Blokpax scraper creates Seller records for wallet addresses
- [ ] Daily inventory snapshot job runs without errors
- [ ] SKU mapping accuracy >90% for ShootStrayt format

---

## CSV Import Schema

### Required Columns
```csv
platform,seller_id,sku,quantity,price,notes
shootstrayt,shootstrayt,WOTF-EXISTENCE-143-RAR-CP,5,24.99,
ebay,cardshop123,Phoenix Quill Formless Foil,3,45.00,auction listing
```

### Column Definitions
| Column | Type | Required | Description |
|--------|------|----------|-------------|
| platform | string | Yes | Source platform (ebay, blokpax, shootstrayt) |
| seller_id | string | Yes | Platform-specific seller identifier |
| sku | string | Yes | Product SKU or card name |
| quantity | int | Yes | Number of items |
| price | float | No | Unit price (null = "contact for price") |
| notes | string | No | Additional notes |

### Validation Rules
- platform must be in allowed list
- quantity must be > 0
- price must be >= 0 if provided
- sku must match existing card OR auto-map with confidence

---

## Tasks

### T3.1 — CSV Import Utility
Script to import seller inventory from CSV files.

**UOWs**:
- U3.1.1: Create CSV schema validator (2h)
- U3.1.2: Create SKU resolver service (4h)
- U3.1.3: Implement CSV import logic (4h)
- U3.1.4: Create CSV import CLI script (2h)

### T3.2 — ShootStrayt Integration
Scraper for ShootStrayt inventory and SKU parsing.

**UOWs**:
- U3.2.1: Create ShootStrayt SKU parser (3h)
- U3.2.2: Create Card lookup by set+number (3h)
- U3.2.3: Create ShootStrayt scraper (4h)
- U3.2.4: Create ShootStrayt import script (3h)

### T3.3 — Update eBay Scraper
Modify eBay scraper to create/update Seller records.

**UOWs**:
- U3.3.1: Add seller extraction to eBay scraper (2h)
- U3.3.2: Implement get_or_create_seller utility (2h)
- U3.3.3: Update eBay scraper to use Seller model (2h)
- U3.3.4: Test eBay scraper with Seller integration (2h)

### T3.4 — Update Blokpax Scraper
Modify Blokpax scraper to create/update Seller records.

**UOWs**:
- U3.4.1: Add seller extraction to Blokpax scraper (1h)
- U3.4.2: Update Blokpax scraper to create Sellers (2h)
- U3.4.3: Test Blokpax scraper integration (1.5h)

### T3.5 — Inventory Snapshot Background Job
Daily job to snapshot current seller inventory state.

**UOWs**:
- U3.5.1: Create snapshot generation function (4h)
- U3.5.2: Add snapshot job to scheduler (2h)
- U3.5.3: Create manual snapshot CLI script (1.5h)

---

## ShootStrayt SKU Format

```
WOTF-EXISTENCE-143-RAR-CP
│    │         │   │   └── Treatment: CP=Classic Paper, CF=Classic Foil, FF=Formless Foil, OCM=OCM
│    │         │   └────── Rarity: COM, UNC, RAR, EPR, LEG, GOD
│    │         └────────── Card Number: Collector number
│    └──────────────────── Set Name: EXISTENCE, WONDER, etc.
└────────────────────────── Product: WOTF (Wonders of the First)
```

### Parser Logic
```python
def parse_shootstrayt_sku(sku: str) -> dict:
    """
    Parse ShootStrayt SKU format.
    Returns: {product, set, number, rarity, treatment} or None if invalid
    """
    parts = sku.split('-')
    if len(parts) != 5:
        return None

    treatment_map = {
        'CP': 'Classic Paper',
        'CF': 'Classic Foil',
        'FF': 'Formless Foil',
        'OCM': 'OCM Serialized'
    }

    return {
        'product': parts[0],
        'set': parts[1],
        'number': parts[2],
        'rarity': parts[3],
        'treatment': treatment_map.get(parts[4], parts[4])
    }
```

---

## Required Documentation

- `/docs/CSV_IMPORT.md` - CSV schema, validation rules, error handling
- `/docs/SHOOTSTRAYT_INTEGRATION.md` - Scraper usage, SKU format parsing
- `/docs/SCRAPER_UPDATES.md` - Changes to eBay/Blokpax scrapers
