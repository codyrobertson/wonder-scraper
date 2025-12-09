# EPIC-5: Database Schema & Models

**Status**: Planned
**Sprint**: 1-2
**Priority**: Critical (Foundational)
**Dependencies**: None

---

## Objective

Define and implement the core data architecture for multi-source seller tracking.

## User Impact

Foundational - enables all future seller features.

## Tech Scope

- SQLModel models
- Alembic migrations
- Foreign keys and indexes
- Data migration scripts

---

## Done-When Criteria

- [ ] All new tables exist in production database
- [ ] Models have proper relationships and constraints
- [ ] Migration is reversible
- [ ] No performance degradation on existing queries
- [ ] >95% of existing MarketPrice records have seller_id populated
- [ ] Unit tests for all model relationships

---

## New Models

### Seller
Tracks sellers across platforms with unique (platform, platform_seller_id) constraint.

```python
class Seller(SQLModel, table=True):
    id: int  # PK
    platform: str  # ebay, blokpax, shootstrayt (indexed)
    platform_seller_id: str  # username/wallet/id (indexed)
    display_name: Optional[str]
    feedback_score: Optional[int]
    feedback_percent: Optional[float]
    metadata: Optional[dict]  # JSON field for platform-specific data
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    # Unique constraint on (platform, platform_seller_id)
```

### SellerInventory
Current inventory holdings per seller, per card, per treatment.

```python
class SellerInventory(SQLModel, table=True):
    id: int  # PK
    seller_id: int  # FK to Seller (indexed)
    card_id: int  # FK to Card (indexed)
    treatment: str = "Classic Paper"
    quantity: int = 1
    price: Optional[float]
    platform_listing_id: Optional[str]
    listed_at: Optional[datetime]
    updated_at: datetime

    # Unique constraint on (seller_id, card_id, treatment, platform_listing_id)
    # Composite index on (seller_id, card_id)
```

### SKUMapping
Maps external SKUs to internal Card IDs with confidence scoring.

```python
class SKUMapping(SQLModel, table=True):
    id: int  # PK
    platform: str  # indexed
    external_sku: str  # indexed
    card_id: int  # FK to Card (indexed)
    treatment: Optional[str]
    confidence_score: float = 1.0  # 0.0-1.0
    verified: bool = False  # indexed
    created_by: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Unique constraint on (platform, external_sku)
```

### InventorySnapshot
Daily snapshots for historical tracking.

```python
class InventorySnapshot(SQLModel, table=True):
    id: int  # PK
    seller_id: int  # FK to Seller (indexed)
    card_id: int  # FK to Card (indexed)
    treatment: str = "Classic Paper"
    quantity: int
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    snapshot_date: date  # indexed
    created_at: datetime

    # Unique constraint on (seller_id, card_id, treatment, snapshot_date)
    # Composite index on (card_id, snapshot_date)
```

### MarketPrice Update
Add nullable seller_id FK for backward compatibility.

```python
# Add to existing MarketPrice model:
seller_id: Optional[int] = Field(default=None, foreign_key="seller.id", index=True)
```

---

## Tasks

### T1.1 — Design Seller Model
Create `/app/models/seller.py` with Seller model.

**UOWs**:
- U1.1.1: Create Seller SQLModel class (2h)
- U1.1.2: Add Seller to models `__init__.py` (15m)

### T1.2 — Design SellerInventory Model
Add SellerInventory to track holdings.

**UOWs**:
- U1.2.1: Create SellerInventory SQLModel class (2h)
- U1.2.2: Add SellerInventory to exports (10m)

### T1.3 — Design SKUMapping Model
Map external SKUs to Card IDs.

**UOWs**:
- U1.3.1: Create SKUMapping SQLModel class (2h)
- U1.3.2: Add SKUMapping to exports (10m)

### T1.4 — Design InventorySnapshot Model
Daily snapshots for time-series analysis.

**UOWs**:
- U1.4.1: Create InventorySnapshot SQLModel class (2h)
- U1.4.2: Add InventorySnapshot to exports (10m)

### T1.5 — Update MarketPrice Model
Add seller_id FK while preserving backward compatibility.

**UOWs**:
- U1.5.1: Add seller_id field to MarketPrice (1h)
- U1.5.2: Add seller_id index (30m)

### T1.6 — Create Alembic Migration
Generate database migration.

**UOWs**:
- U1.6.1: Generate autogenerate migration (1h)
- U1.6.2: Test migration upgrade/downgrade (2h)

### T1.7 — Data Migration Script
Backfill Seller table from existing seller_name data.

**UOWs**:
- U1.7.1: Create seller normalization utility (2h)
- U1.7.2: Create backfill migration script (4h)
- U1.7.3: Test migration script on staging data (2h)

### T1.8 — Model Unit Tests
Test relationships, constraints, edge cases.

**UOWs**:
- U1.8.1: Create test_seller_models.py (3h)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Seller name normalization challenges | High | Conservative matching, manual review for edge cases |
| Duplicate seller detection accuracy | High | High threshold matching, log for review |
| Migration rollback complexity | Medium | Test on staging, have rollback plan |
| Performance during backfill | Medium | Run during low-traffic, batch updates |

---

## Required Documentation

- `/docs/ARCHITECTURE.md` - ERD diagram showing relationships
- `/docs/MIGRATION_PLAN.md` - Step-by-step migration runbook
