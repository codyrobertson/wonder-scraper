# EPIC: Multi-Source Seller & Inventory Integration

**Status**: Planning
**Priority**: High
**Owner**: TBD
**Created**: 2025-12-08

---

## A. Goals & Context

### Product Goals
- **Unified Seller Tracking**: Track sellers across multiple platforms (eBay, Blokpax, ShootStrayt, future integrations) with a single Seller entity
- **Inventory Management**: Monitor stock levels per seller, per card, per treatment to identify supply trends
- **SKU Mapping System**: Map external SKUs (e.g., ShootStrayt's `WOTF-EXISTENCE-143-RAR-CP`) to internal Card IDs
- **Multi-Source ETL**: Support CSV imports, direct API integrations, and scraper-based ingestion
- **Supply Analytics**: Enable insights like "seller concentration", "supply diversity", "inventory velocity"

### Technical Goals
- **Normalize seller data** from string fields to dedicated Seller model with relationships
- **Extensible architecture** for adding new platforms without refactoring core models
- **Backward compatibility** during migration from `seller_name` strings to Seller FK
- **Audit trail** for inventory changes and SKU mappings
- **Performance** at scale (100K+ listings, 1K+ sellers)

### Constraints
- Must maintain existing MarketPrice/MarketSnapshot functionality during migration
- Cannot break current scrapers (eBay, Blokpax) during rollout
- Frontend should continue working with minimal changes
- Database migrations must be reversible

### Assumptions
- ShootStrayt SKU format is stable: `{PRODUCT}-{SET}-{NUMBER}-{RARITY}-{TREATMENT}`
- Seller identity can be uniquely identified by (platform, platform_seller_id) tuple
- eBay seller names and Blokpax wallet addresses are stable identifiers
- Inventory snapshots taken daily are sufficient (not real-time)

### Questions / Missing Info

**CRITICAL - Must answer before implementation:**
1. **ShootStrayt API Access**: Do we have API credentials? Is there documentation?
2. **SKU Format Variations**: Are there other SKU formats besides ShootStrayt's? (TCGPlayer, etc.)
3. **Inventory Update Frequency**: How often should we poll seller inventories? (Daily, hourly, on-demand)
4. **Seller Identity Merging**: What if a seller operates on multiple platforms with different names?
5. **CSV Import Schema**: What columns/format will CSV imports use? Who generates them?
6. **Historical Data**: Should we backfill historical seller data from existing MarketPrice records?
7. **Admin UI Priority**: Is this needed for MVP or can we start with API-only + scripts?

**NICE-TO-HAVE - Can defer:**
- Seller reputation scoring algorithms
- Automated SKU conflict resolution
- Real-time inventory webhooks
- Seller contact information storage

---

## B. Phase Plan

### Phase 1: Foundation & Data Architecture (Sprint 1-2)
**Goal**: Establish core data models, migration strategy, and database layer
**Timeline**: 2 weeks

**In-Scope**:
- New database models: Seller, SellerInventory, SKUMapping, InventorySnapshot
- Alembic migration to add new tables
- Data migration script to populate Seller table from existing MarketPrice.seller_name
- Update MarketPrice model to add seller_id FK (nullable during migration)
- Basic CRUD utilities for new models

**Out-of-Scope**:
- API endpoints (Phase 2)
- ETL pipelines (Phase 3)
- Admin UI (Phase 4)
- Scraper updates (deferred to Phase 3)

**Exit Criteria**:
- [ ] All new tables created in database
- [ ] Migration script successfully backfills Seller table with 95%+ of existing sellers
- [ ] MarketPrice has seller_id FK populated for 80%+ of records
- [ ] No existing queries broken (backward compatible)
- [ ] Unit tests for all model relationships

**Risks**:
- Seller name normalization challenges (eBay: "seller_123" vs Blokpax: "0x1234...")
- Duplicate seller detection accuracy
- Migration rollback complexity if issues arise

---

### Phase 2: API Layer (Sprint 3)
**Goal**: RESTful API endpoints for managing sellers, inventory, and SKU mappings
**Timeline**: 1 week

**In-Scope**:
- GET/POST/PUT/DELETE /api/sellers
- GET/POST /api/sellers/{id}/inventory
- GET/POST /api/sku-mappings
- GET /api/inventory/snapshots
- OpenAPI documentation
- Authentication/authorization for admin endpoints

**Out-of-Scope**:
- Complex seller analytics endpoints (deferred to Phase 5)
- Bulk import endpoints (Phase 3)
- Real-time inventory webhooks

**Exit Criteria**:
- [ ] All CRUD operations working with 200/201/400/404 responses
- [ ] Pagination implemented for list endpoints
- [ ] API key authentication enforced for write operations
- [ ] Swagger docs generated and accurate
- [ ] Integration tests for all endpoints (80%+ coverage)

**Dependencies**:
- Phase 1 must be complete (models exist)

---

### Phase 3: ETL Pipeline & Integrations (Sprint 4-5)
**Goal**: Build data ingestion pipelines for CSV, ShootStrayt API, and update existing scrapers
**Timeline**: 2 weeks

**In-Scope**:
- CSV import script with validation and SKU mapping
- ShootStrayt API client (if API available)
- Update eBay scraper to create/update Seller records
- Update Blokpax scraper to create/update Seller records
- Inventory snapshot background job (daily)
- SKU auto-mapping heuristics (fuzzy matching card names)

**Out-of-Scope**:
- Real-time streaming ingestion
- Automatic SKU conflict resolution (manual for MVP)
- TCGPlayer/other platform integrations (future)

**Exit Criteria**:
- [ ] CSV import processes 1000-row file in <30 seconds
- [ ] ShootStrayt integration fetches inventory successfully (if API exists)
- [ ] eBay scraper creates Seller records for new sellers
- [ ] Blokpax scraper creates Seller records for new wallet addresses
- [ ] Daily inventory snapshot job runs without errors
- [ ] SKU mapping accuracy >90% for ShootStrayt format

**Dependencies**:
- Phase 2 complete (API endpoints exist for data writes)
- Answers to Questions 1, 5, 6 above

---

### Phase 4: Admin Tools & Management UI (Sprint 6)
**Goal**: Build admin interfaces for managing integrations and reviewing data quality
**Timeline**: 1 week

**In-Scope**:
- Admin UI page: Seller management (view, edit, merge duplicates)
- Admin UI page: SKU mapping review (approve/reject auto-mappings)
- Admin UI page: Inventory snapshots (historical trends)
- CSV upload form with preview and validation
- Seller merge tool (combine duplicate seller profiles)

**Out-of-Scope**:
- Public-facing seller profiles
- Advanced seller analytics dashboards (Phase 5)
- Automated duplicate detection UI

**Exit Criteria**:
- [ ] Admin can upload CSV and see preview before import
- [ ] Admin can manually create/edit SKU mappings
- [ ] Admin can merge duplicate seller profiles
- [ ] Admin can view inventory snapshots by seller/card
- [ ] All forms have proper validation and error messages

**Dependencies**:
- Phase 3 complete (ETL pipelines exist)
- Frontend architecture ready for new admin routes

---

### Phase 5: Analytics & Observability (Sprint 7)
**Goal**: Surface seller and inventory insights through API and UI
**Timeline**: 1 week

**In-Scope**:
- Seller analytics endpoints (inventory size, sales volume, market share)
- Supply diversity metrics (# of sellers per card, concentration index)
- Inventory velocity tracking (days to sell)
- Logging and monitoring for ETL jobs
- Data quality dashboards (SKU mapping accuracy, unmapped listings)

**Out-of-Scope**:
- Predictive analytics (ML-based supply forecasting)
- Seller reputation scoring
- Alerts/notifications for inventory changes

**Exit Criteria**:
- [ ] API returns seller metrics (total inventory, 30d sales, etc.)
- [ ] Dashboard shows supply diversity by card
- [ ] ETL job logs visible in monitoring system
- [ ] Data quality dashboard shows <5% unmapped SKUs

**Dependencies**:
- Phase 4 complete (admin tools exist)
- Sufficient historical data accumulated (2+ weeks of snapshots)

---

## C. Epics & Tasks

### EPIC-1: Database Schema & Models
**Objective**: Define and implement the core data architecture for multi-source seller tracking
**User Impact**: Foundational - enables all future seller features
**Tech Scope**: SQLModel models, Alembic migrations, foreign keys, indexes
**Dependencies**: None (foundational work)

**Done-When**:
- All new tables exist in production database
- Models have proper relationships and constraints
- Migration is reversible
- No performance degradation on existing queries

**Docs Required**:
- **/docs/ARCHITECTURE.md** - ERD diagram showing Seller, SellerInventory, SKUMapping relationships
- **/docs/MIGRATION_PLAN.md** - Step-by-step migration runbook for production

---

### EPIC-2: Seller Management API
**Objective**: RESTful API for CRUD operations on sellers and inventory
**User Impact**: Admins can manage seller data programmatically
**Tech Scope**: FastAPI endpoints, Pydantic schemas, authentication, OpenAPI docs
**Dependencies**: EPIC-1 (models must exist)

**Done-When**:
- All CRUD endpoints return proper HTTP status codes
- API documented in Swagger UI
- Rate limiting implemented
- 80%+ test coverage

**Docs Required**:
- **/docs/API_REFERENCE.md** - Endpoint specifications with request/response examples
- **/docs/AUTHENTICATION.md** - API key usage and permission model

---

### EPIC-3: ETL & Data Ingestion
**Objective**: Build pipelines to ingest seller data from multiple sources
**User Impact**: Automated seller/inventory tracking without manual data entry
**Tech Scope**: CSV parser, API clients, scraper updates, background jobs
**Dependencies**: EPIC-2 (API layer for writes), ShootStrayt API access (if applicable)

**Done-When**:
- CSV import script handles 10K rows without errors
- Scrapers create/update Seller records on each run
- Daily inventory snapshot job completes in <5 minutes
- SKU mapping success rate >90%

**Docs Required**:
- **/docs/CSV_IMPORT.md** - CSV schema, validation rules, error handling
- **/docs/SHOOTSTRAYT_INTEGRATION.md** - API client usage, SKU format parsing
- **/docs/SCRAPER_UPDATES.md** - Changes to eBay/Blokpax scrapers

---

### EPIC-4: Admin UI
**Objective**: Web interface for managing sellers, SKUs, and inventory
**User Impact**: Admins can visually manage integrations without API calls
**Tech Scope**: React components, forms, tables, TanStack Router routes
**Dependencies**: EPIC-3 (data ingestion must be working)

**Done-When**:
- Admin can perform all operations from UI (no API calls needed)
- Forms have real-time validation
- CSV upload shows preview before import
- Seller merge tool successfully combines profiles

**Docs Required**:
- **/docs/ADMIN_UI.md** - User guide for admin features
- **/docs/UI_COMPONENTS.md** - Reusable component documentation

---

### EPIC-5: Observability & Analytics
**Objective**: Surface insights about sellers, inventory, and data quality
**User Impact**: Users can make informed decisions based on supply metrics
**Tech Scope**: Analytics endpoints, aggregation queries, monitoring dashboards
**Dependencies**: EPIC-4 (requires historical data from Phase 3+)

**Done-When**:
- Seller analytics API returns metrics in <500ms
- Data quality dashboard shows <5% error rate
- ETL job logs queryable via monitoring UI
- Supply diversity metrics match manual calculations

**Docs Required**:
- **/docs/ANALYTICS.md** - Metric definitions and calculation methods
- **/docs/MONITORING.md** - Dashboard access, alerting setup

---

## D. Units of Work (UOW)

### EPIC-1: Database Schema & Models

---

#### Task T1.1 — Design Seller Model
**Belongs to**: EPIC-1
**Description**: Define the Seller model to track sellers across platforms

**Acceptance Criteria**:
- Model includes fields: id, platform, platform_seller_id, display_name, metadata
- Unique constraint on (platform, platform_seller_id)
- Indexes on platform and created_at
- Supports JSON metadata field for platform-specific data

**Required Docs**:
- **/docs/ARCHITECTURE.md** - ERD showing Seller relationships

**UOWs**:

- **UOW U1.1.1 — Create Seller SQLModel class**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/models/seller.py` with Seller model having fields: id (PK), platform (str, indexed), platform_seller_id (str, indexed), display_name (str, nullable), feedback_score (int, nullable), feedback_percent (float, nullable), metadata (JSON, nullable), created_at, updated_at. Add unique constraint on (platform, platform_seller_id).
  - Estimate: 2 hours
  - Dependencies: None
  - Acceptance Checks: Model imports without errors, fields match spec, constraint defined

- **UOW U1.1.2 — Add Seller to models __init__.py**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/models/__init__.py` to import and expose Seller model
  - Estimate: 15 minutes
  - Dependencies: U1.1.1
  - Acceptance Checks: `from app.models import Seller` works in Python shell

---

#### Task T1.2 — Design SellerInventory Model
**Belongs to**: EPIC-1
**Description**: Track inventory holdings per seller, per card, per treatment

**Acceptance Criteria**:
- Model includes fields: id, seller_id (FK), card_id (FK), treatment, quantity, price, updated_at
- Unique constraint on (seller_id, card_id, treatment)
- Indexes on seller_id, card_id, updated_at
- Supports NULL price (for "contact for price" listings)

**UOWs**:

- **UOW U1.2.1 — Create SellerInventory SQLModel class**
  - Type: backend
  - Exact Action: Add SellerInventory model to `/Users/Cody/code_projects/wonder-scraper/app/models/seller.py` with fields: id (PK), seller_id (FK to Seller), card_id (FK to Card), treatment (str, default="Classic Paper"), quantity (int, default=1), price (float, nullable), platform_listing_id (str, nullable), listed_at (datetime, nullable), updated_at (datetime). Add unique constraint on (seller_id, card_id, treatment, platform_listing_id). Add composite index on (seller_id, card_id).
  - Estimate: 2 hours
  - Dependencies: U1.1.1
  - Acceptance Checks: Model validates, foreign keys reference correct tables, indexes defined

- **UOW U1.2.2 — Add SellerInventory to exports**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/models/__init__.py` to export SellerInventory
  - Estimate: 10 minutes
  - Dependencies: U1.2.1
  - Acceptance Checks: Import works in test file

---

#### Task T1.3 — Design SKUMapping Model
**Belongs to**: EPIC-1
**Description**: Map external SKUs to internal Card IDs with confidence scoring

**Acceptance Criteria**:
- Model includes: id, platform, external_sku, card_id (FK), treatment, confidence_score, verified, created_by, created_at
- Unique constraint on (platform, external_sku)
- Index on card_id and verified status
- Confidence score 0.0-1.0 (fuzzy match accuracy)

**UOWs**:

- **UOW U1.3.1 — Create SKUMapping SQLModel class**
  - Type: backend
  - Exact Action: Add SKUMapping model to `/Users/Cody/code_projects/wonder-scraper/app/models/seller.py` with fields: id (PK), platform (str, indexed), external_sku (str, indexed), card_id (FK to Card, indexed), treatment (str, nullable), confidence_score (float, default=1.0), verified (bool, default=False, indexed), created_by (str, nullable), notes (str, nullable), created_at, updated_at. Add unique constraint on (platform, external_sku).
  - Estimate: 2 hours
  - Dependencies: U1.1.1
  - Acceptance Checks: Model validates, unique constraint works, confidence_score constrained to 0-1

- **UOW U1.3.2 — Add SKUMapping to exports**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/models/__init__.py` to export SKUMapping
  - Estimate: 10 minutes
  - Dependencies: U1.3.1
  - Acceptance Checks: Import works

---

#### Task T1.4 — Design InventorySnapshot Model
**Belongs to**: EPIC-1
**Description**: Daily snapshots of seller inventory for historical tracking

**Acceptance Criteria**:
- Model includes: id, seller_id (FK), card_id (FK), treatment, quantity, avg_price, snapshot_date
- Composite index on (seller_id, card_id, snapshot_date)
- Index on snapshot_date for time-series queries
- Unique constraint on (seller_id, card_id, treatment, snapshot_date)

**UOWs**:

- **UOW U1.4.1 — Create InventorySnapshot SQLModel class**
  - Type: backend
  - Exact Action: Add InventorySnapshot model to `/Users/Cody/code_projects/wonder-scraper/app/models/seller.py` with fields: id (PK), seller_id (FK to Seller, indexed), card_id (FK to Card, indexed), treatment (str, default="Classic Paper"), quantity (int), avg_price (float, nullable), min_price (float, nullable), max_price (float, nullable), snapshot_date (date, indexed), created_at. Add unique constraint on (seller_id, card_id, treatment, snapshot_date). Add composite index on (card_id, snapshot_date).
  - Estimate: 2 hours
  - Dependencies: U1.1.1
  - Acceptance Checks: Model validates, indexes optimized for time-series queries

- **UOW U1.4.2 — Add InventorySnapshot to exports**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/models/__init__.py` to export InventorySnapshot
  - Estimate: 10 minutes
  - Dependencies: U1.4.1
  - Acceptance Checks: Import works

---

#### Task T1.5 — Update MarketPrice Model
**Belongs to**: EPIC-1
**Description**: Add seller_id FK to MarketPrice while preserving backward compatibility

**Acceptance Criteria**:
- Add nullable seller_id FK to MarketPrice
- Keep seller_name field for backward compatibility
- Create index on seller_id
- Add migration script to backfill seller_id from seller_name

**UOWs**:

- **UOW U1.5.1 — Add seller_id field to MarketPrice**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/models/market.py` to add field `seller_id: Optional[int] = Field(default=None, foreign_key="seller.id", index=True)` after seller_feedback_percent field. Add comment explaining migration strategy.
  - Estimate: 1 hour
  - Dependencies: U1.1.1
  - Acceptance Checks: Model imports successfully, FK relationship valid

- **UOW U1.5.2 — Add seller_id index to MarketPrice __table_args__**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/models/market.py` __table_args__ to add index on seller_id for seller-based queries
  - Estimate: 30 minutes
  - Dependencies: U1.5.1
  - Acceptance Checks: Index appears in table schema

---

#### Task T1.6 — Create Alembic Migration
**Belongs to**: EPIC-1
**Description**: Generate database migration to create new tables and alter MarketPrice

**Acceptance Criteria**:
- Migration creates Seller, SellerInventory, SKUMapping, InventorySnapshot tables
- Migration adds seller_id column to MarketPrice
- Migration is reversible (downgrade drops tables, removes column)
- No data loss in downgrade (seller_name preserved)

**UOWs**:

- **UOW U1.6.1 — Generate autogenerate migration**
  - Type: backend
  - Exact Action: Run `alembic revision --autogenerate -m "Add seller tables and seller_id to MarketPrice"` in `/Users/Cody/code_projects/wonder-scraper/` directory. Review generated migration file in `alembic/versions/` for correctness.
  - Estimate: 1 hour
  - Dependencies: U1.1.2, U1.2.2, U1.3.2, U1.4.2, U1.5.1
  - Acceptance Checks: Migration file generated, upgrade/downgrade functions present

- **UOW U1.6.2 — Test migration upgrade/downgrade**
  - Type: backend
  - Exact Action: Run `alembic upgrade head` on test database, verify tables created. Run `alembic downgrade -1` to rollback, verify tables dropped. Check for SQL errors or constraint violations.
  - Estimate: 2 hours
  - Dependencies: U1.6.1
  - Acceptance Checks: Upgrade succeeds, downgrade succeeds, no data corruption

---

#### Task T1.7 — Data Migration Script
**Belongs to**: EPIC-1
**Description**: Backfill Seller table from existing MarketPrice.seller_name data

**Acceptance Criteria**:
- Script extracts unique (platform, seller_name) tuples from MarketPrice
- Creates Seller records with normalized names
- Updates MarketPrice.seller_id for matched records
- Handles duplicates (case variations, whitespace)
- Logs unmatchable sellers for manual review

**UOWs**:

- **UOW U1.7.1 — Create seller normalization utility**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/services/seller_utils.py` with function `normalize_seller_name(platform: str, seller_name: str) -> str` that lowercases, strips whitespace, handles platform-specific formats (eBay usernames, Blokpax wallet addresses).
  - Estimate: 2 hours
  - Dependencies: None
  - Acceptance Checks: Handles edge cases (None, empty string, Unicode), unit tests pass

- **UOW U1.7.2 — Create backfill migration script**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/scripts/migrate_sellers.py` that: 1) Queries distinct (platform, seller_name) from MarketPrice, 2) Normalizes names using seller_utils, 3) Creates Seller records with deduplication, 4) Updates MarketPrice.seller_id via bulk update, 5) Logs coverage stats (% matched) and unmatched sellers to file.
  - Estimate: 4 hours
  - Dependencies: U1.7.1, U1.6.2 (migration applied)
  - Acceptance Checks: Script runs without errors, >95% of MarketPrice records get seller_id, logs detailed stats

- **UOW U1.7.3 — Test migration script on staging data**
  - Type: backend
  - Exact Action: Run migrate_sellers.py on staging database with production data snapshot. Verify seller_id population, check for constraint violations, review unmatched seller log.
  - Estimate: 2 hours
  - Dependencies: U1.7.2
  - Acceptance Checks: No errors, seller_id coverage >95%, unmatched list reviewed

---

#### Task T1.8 — Model Unit Tests
**Belongs to**: EPIC-1
**Description**: Test model relationships, constraints, and edge cases

**Acceptance Criteria**:
- Test Seller unique constraint on (platform, platform_seller_id)
- Test SellerInventory FK relationships
- Test SKUMapping confidence_score validation
- Test InventorySnapshot unique constraint
- 100% model coverage

**UOWs**:

- **UOW U1.8.1 — Create test_seller_models.py**
  - Type: tests
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/tests/models/test_seller_models.py` with test cases for: Seller creation, unique constraint violations, SellerInventory FK integrity, SKUMapping confidence_score bounds, InventorySnapshot date uniqueness.
  - Estimate: 3 hours
  - Dependencies: U1.6.2 (tables exist in test DB)
  - Acceptance Checks: All tests pass, pytest coverage >95% for seller.py

---

### EPIC-2: Seller Management API

---

#### Task T2.1 — Seller CRUD Endpoints
**Belongs to**: EPIC-2
**Description**: RESTful API for managing Seller records

**Acceptance Criteria**:
- GET /api/sellers (list with pagination, filters)
- GET /api/sellers/{id} (detail)
- POST /api/sellers (create)
- PUT /api/sellers/{id} (update)
- DELETE /api/sellers/{id} (soft delete)
- All endpoints return proper HTTP status codes

**UOWs**:

- **UOW U2.1.1 — Create Pydantic schemas for Seller**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/api/schemas/seller.py` with classes: SellerBase (base fields), SellerCreate (for POST), SellerUpdate (for PUT), SellerRead (for responses with relationships), SellerList (paginated response).
  - Estimate: 2 hours
  - Dependencies: U1.1.1
  - Acceptance Checks: Schemas validate correctly, support nested relationships

- **UOW U2.1.2 — Create /api/sellers router**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/api/sellers.py` with FastAPI router. Implement GET /sellers (with pagination, platform filter), GET /sellers/{id}, POST /sellers (with duplicate check), PUT /sellers/{id}, DELETE /sellers/{id} (soft delete by setting is_active=False).
  - Estimate: 4 hours
  - Dependencies: U2.1.1
  - Acceptance Checks: All endpoints return 200/201/400/404, pagination works, filters apply

- **UOW U2.1.3 — Add sellers router to main app**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/main.py` (or API router aggregator) to include sellers router at `/api/sellers` prefix.
  - Estimate: 30 minutes
  - Dependencies: U2.1.2
  - Acceptance Checks: Endpoints accessible at /api/sellers, OpenAPI docs show routes

- **UOW U2.1.4 — Add authentication to write operations**
  - Type: backend
  - Exact Action: Edit sellers.py endpoints to require API key authentication (using existing deps.py get_api_key dependency) for POST/PUT/DELETE operations. GET remains public.
  - Estimate: 1 hour
  - Dependencies: U2.1.2
  - Acceptance Checks: Unauthenticated POST returns 401, valid API key works

---

#### Task T2.2 — Inventory Endpoints
**Belongs to**: EPIC-2
**Description**: API for querying and updating seller inventory

**Acceptance Criteria**:
- GET /api/sellers/{id}/inventory (current inventory)
- POST /api/sellers/{id}/inventory (add/update items)
- GET /api/inventory/search (search across all sellers)
- Response includes card details and pricing

**UOWs**:

- **UOW U2.2.1 — Create SellerInventory schemas**
  - Type: backend
  - Exact Action: Add to `/Users/Cody/code_projects/wonder-scraper/app/api/schemas/seller.py`: InventoryItemBase, InventoryItemCreate, InventoryItemUpdate, InventoryItemRead (with nested Card data).
  - Estimate: 2 hours
  - Dependencies: U2.1.1
  - Acceptance Checks: Schemas validate, nested Card relationship works

- **UOW U2.2.2 — Implement GET /sellers/{id}/inventory**
  - Type: backend
  - Exact Action: Add endpoint to sellers.py that queries SellerInventory filtered by seller_id, joins Card table, returns paginated list with card names/images.
  - Estimate: 2 hours
  - Dependencies: U2.2.1, U2.1.2
  - Acceptance Checks: Returns inventory items with card details, pagination works

- **UOW U2.2.3 — Implement POST /sellers/{id}/inventory**
  - Type: backend
  - Exact Action: Add endpoint to sellers.py that accepts list of inventory items (card_id, treatment, quantity, price), performs upsert on unique constraint (seller_id, card_id, treatment), updates updated_at timestamp.
  - Estimate: 3 hours
  - Dependencies: U2.2.1, U2.1.2
  - Acceptance Checks: Creates new items, updates existing, handles conflicts gracefully

- **UOW U2.2.4 — Implement GET /api/inventory/search**
  - Type: backend
  - Exact Action: Create new endpoint (could be in sellers.py or separate inventory.py) that searches SellerInventory by card_id, treatment, seller_id (optional filters), returns results with seller details.
  - Estimate: 2 hours
  - Dependencies: U2.2.1
  - Acceptance Checks: Filters work, returns seller info, pagination implemented

---

#### Task T2.3 — SKU Mapping Endpoints
**Belongs to**: EPIC-2
**Description**: API for managing SKU mappings

**Acceptance Criteria**:
- GET /api/sku-mappings (list with filters)
- POST /api/sku-mappings (create mapping)
- PUT /api/sku-mappings/{id} (update/verify mapping)
- DELETE /api/sku-mappings/{id} (remove mapping)
- GET /api/sku-mappings/resolve?platform={}&sku={} (lookup card by SKU)

**UOWs**:

- **UOW U2.3.1 — Create SKUMapping schemas**
  - Type: backend
  - Exact Action: Add to seller.py schemas: SKUMappingBase, SKUMappingCreate, SKUMappingUpdate, SKUMappingRead (with nested Card).
  - Estimate: 1.5 hours
  - Dependencies: U2.1.1
  - Acceptance Checks: Schemas include all fields, confidence_score validated

- **UOW U2.3.2 — Create /api/sku-mappings router**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/api/sku_mappings.py` with endpoints: GET /sku-mappings (filter by platform, verified status), POST /sku-mappings (with duplicate check), PUT /sku-mappings/{id} (update confidence/verified), DELETE /sku-mappings/{id}.
  - Estimate: 3 hours
  - Dependencies: U2.3.1
  - Acceptance Checks: CRUD operations work, filters apply

- **UOW U2.3.3 — Implement GET /sku-mappings/resolve**
  - Type: backend
  - Exact Action: Add endpoint to sku_mappings.py that queries SKUMapping by (platform, external_sku), returns Card if found (404 if not), prioritizes verified=True mappings over unverified.
  - Estimate: 2 hours
  - Dependencies: U2.3.2
  - Acceptance Checks: Returns card for valid SKU, 404 for unmapped, prioritizes verified

- **UOW U2.3.4 — Add sku-mappings router to main app**
  - Type: backend
  - Exact Action: Edit main.py to include sku_mappings router at /api/sku-mappings.
  - Estimate: 30 minutes
  - Dependencies: U2.3.2
  - Acceptance Checks: Routes accessible, docs updated

---

#### Task T2.4 — Inventory Snapshot Endpoints
**Belongs to**: EPIC-2
**Description**: API for querying historical inventory snapshots

**Acceptance Criteria**:
- GET /api/inventory/snapshots (query by seller, card, date range)
- Response includes time-series data for charting

**UOWs**:

- **UOW U2.4.1 — Create InventorySnapshot schemas**
  - Type: backend
  - Exact Action: Add to seller.py schemas: SnapshotRead (with seller/card details), SnapshotList (paginated).
  - Estimate: 1.5 hours
  - Dependencies: U2.1.1
  - Acceptance Checks: Schemas support date filtering, nested relationships

- **UOW U2.4.2 — Implement GET /inventory/snapshots**
  - Type: backend
  - Exact Action: Add endpoint to inventory.py (or sellers.py) that queries InventorySnapshot with filters: seller_id, card_id, start_date, end_date. Returns time-series data sorted by snapshot_date.
  - Estimate: 2 hours
  - Dependencies: U2.4.1
  - Acceptance Checks: Filters work, time-series format correct, efficient query

---

#### Task T2.5 — API Integration Tests
**Belongs to**: EPIC-2
**Description**: End-to-end tests for all API endpoints

**Acceptance Criteria**:
- Test all CRUD operations with valid/invalid data
- Test authentication enforcement
- Test pagination and filtering
- Test error responses (400, 404, 401)
- 80%+ coverage on API routes

**UOWs**:

- **UOW U2.5.1 — Create test_sellers_api.py**
  - Type: tests
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/tests/api/test_sellers_api.py` with test cases for GET/POST/PUT/DELETE /sellers, including auth tests, validation tests, pagination tests.
  - Estimate: 3 hours
  - Dependencies: U2.1.2
  - Acceptance Checks: All endpoints tested, >80% coverage

- **UOW U2.5.2 — Create test_inventory_api.py**
  - Type: tests
  - Exact Action: Create tests/api/test_inventory_api.py with tests for inventory endpoints, including upsert logic, search filters, snapshot queries.
  - Estimate: 3 hours
  - Dependencies: U2.2.4, U2.4.2
  - Acceptance Checks: All inventory endpoints tested

- **UOW U2.5.3 — Create test_sku_mappings_api.py**
  - Type: tests
  - Exact Action: Create tests/api/test_sku_mappings_api.py with tests for SKU CRUD, resolve endpoint, verified prioritization.
  - Estimate: 2 hours
  - Dependencies: U2.3.3
  - Acceptance Checks: All SKU endpoints tested, resolve logic validated

---

### EPIC-3: ETL & Data Ingestion

---

#### Task T3.1 — CSV Import Utility
**Belongs to**: EPIC-3
**Description**: Script to import seller inventory from CSV files

**Acceptance Criteria**:
- Supports columns: platform, seller_identifier, sku, quantity, price, notes
- Validates data (SKU exists, price valid, quantity > 0)
- Auto-creates Seller if not exists
- Maps SKUs to Card IDs (creates SKUMapping if confidence high)
- Upserts SellerInventory records
- Generates import report (success/failure counts)

**UOWs**:

- **UOW U3.1.1 — Create CSV schema validator**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/services/csv_importer.py` with function `validate_csv_schema(file_path: str) -> dict` that checks for required columns, validates data types, returns dict of {valid: bool, errors: [...]}.
  - Estimate: 2 hours
  - Dependencies: None
  - Acceptance Checks: Detects missing columns, type mismatches, returns clear errors

- **UOW U3.1.2 — Create SKU resolver service**
  - Type: backend
  - Exact Action: Add function to csv_importer.py: `resolve_sku(platform: str, sku: str) -> Optional[int]` that: 1) Checks SKUMapping table, 2) Falls back to fuzzy card name matching if unmapped, 3) Returns card_id or None, 4) Creates SKUMapping if confidence >0.9.
  - Estimate: 4 hours
  - Dependencies: U1.3.1 (SKUMapping model)
  - Acceptance Checks: Returns card_id for known SKUs, fuzzy matches common variants

- **UOW U3.1.3 — Implement CSV import logic**
  - Type: backend
  - Exact Action: Add function `import_csv(file_path: str, platform: str) -> dict` to csv_importer.py that: 1) Validates CSV, 2) For each row: find/create Seller, resolve SKU to card_id, upsert SellerInventory, 3) Returns report with counts (total, success, failed, skipped) and error details.
  - Estimate: 4 hours
  - Dependencies: U3.1.1, U3.1.2
  - Acceptance Checks: Processes 1000-row CSV in <30 seconds, handles errors gracefully

- **UOW U3.1.4 — Create CSV import CLI script**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/scripts/import_seller_csv.py` that accepts args (--file, --platform, --dry-run), calls csv_importer.import_csv(), prints report, optionally writes report to file.
  - Estimate: 2 hours
  - Dependencies: U3.1.3
  - Acceptance Checks: Script runs, --dry-run shows preview, actual import updates DB

---

#### Task T3.2 — ShootStrayt Integration
**Belongs to**: EPIC-3
**Description**: API client for ShootStrayt inventory and SKU parsing

**Acceptance Criteria**:
- Parse ShootStrayt SKU format: WOTF-EXISTENCE-143-RAR-CP
- Fetch inventory via API (if available) or accept manual CSV
- Map SKUs to Card IDs using set+number
- Create Seller record for ShootStrayt
- Update SellerInventory daily

**UOWs**:

- **UOW U3.2.1 — Create ShootStrayt SKU parser**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/services/shootstrayt_parser.py` with function `parse_shootstrayt_sku(sku: str) -> dict` that extracts {product, set, number, rarity, treatment} from SKU format. Handle edge cases (missing parts, unknown formats).
  - Estimate: 3 hours
  - Dependencies: None
  - Acceptance Checks: Parses valid SKUs correctly, returns None for invalid, unit tests pass

- **UOW U3.2.2 — Create Card lookup by set+number**
  - Type: backend
  - Exact Action: Add function to shootstrayt_parser.py: `find_card_by_identifier(set_name: str, number: str) -> Optional[int]` that queries Card table. ShootStrayt uses collector numbers which may not exist yet - needs mapping strategy (discuss with team).
  - Estimate: 3 hours
  - Dependencies: U3.2.1
  - Acceptance Checks: Finds cards when number exists, returns None otherwise

- **UOW U3.2.3 — Create ShootStrayt API client (if API exists)**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/scraper/shootstrayt.py` with async functions to fetch inventory. Structure TBD based on API documentation. If no API, skip this UOW and rely on CSV import.
  - Estimate: 4 hours (conditional on API availability)
  - Dependencies: Answer to Question 1 (API access)
  - Acceptance Checks: Fetches inventory successfully, handles auth, rate limiting

- **UOW U3.2.4 — Create ShootStrayt import script**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/scripts/import_shootstrayt.py` that: 1) Fetches inventory (API or CSV), 2) Parses SKUs, 3) Creates/updates Seller for ShootStrayt, 4) Upserts SellerInventory, 5) Creates SKUMappings, 6) Logs report.
  - Estimate: 3 hours
  - Dependencies: U3.2.1, U3.2.2, U3.2.3 (or U3.1.3 for CSV)
  - Acceptance Checks: Script completes without errors, inventory updated

---

#### Task T3.3 — Update eBay Scraper
**Belongs to**: EPIC-3
**Description**: Modify eBay scraper to create/update Seller records

**Acceptance Criteria**:
- Extract seller info from eBay listings (name, feedback score, feedback %)
- Create Seller record if not exists (platform="ebay", platform_seller_id=seller_name)
- Set MarketPrice.seller_id on new/updated listings
- Maintain backward compatibility (seller_name still populated)

**UOWs**:

- **UOW U3.3.1 — Add seller extraction to eBay scraper**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/scraper/ebay.py`, locate parsing logic for listings, add extraction of seller_name, seller_feedback_score, seller_feedback_percent from HTML/API response. Create dict {name, score, percent}.
  - Estimate: 2 hours
  - Dependencies: U1.1.1 (Seller model exists)
  - Acceptance Checks: Seller data extracted correctly from test listings

- **UOW U3.3.2 — Implement get_or_create_seller utility**
  - Type: backend
  - Exact Action: Add function to seller_utils.py: `get_or_create_seller(session: Session, platform: str, platform_seller_id: str, **kwargs) -> Seller` that queries Seller by (platform, platform_seller_id), creates if not exists, updates metadata if exists.
  - Estimate: 2 hours
  - Dependencies: U1.1.1
  - Acceptance Checks: Creates new sellers, reuses existing, handles concurrent access

- **UOW U3.3.3 — Update eBay scraper to use Seller model**
  - Type: backend
  - Exact Action: Edit ebay.py to call get_or_create_seller() when creating MarketPrice records, set MarketPrice.seller_id = seller.id. Keep seller_name populated for backward compat.
  - Estimate: 2 hours
  - Dependencies: U3.3.1, U3.3.2
  - Acceptance Checks: New listings have seller_id set, seller_name still populated

- **UOW U3.3.4 — Test eBay scraper with Seller integration**
  - Type: tests
  - Exact Action: Run eBay scraper on test card, verify Seller records created, MarketPrice.seller_id populated, no duplicates, no errors.
  - Estimate: 2 hours
  - Dependencies: U3.3.3
  - Acceptance Checks: Scraper works as before, sellers tracked correctly

---

#### Task T3.4 — Update Blokpax Scraper
**Belongs to**: EPIC-3
**Description**: Modify Blokpax scraper to create/update Seller records

**Acceptance Criteria**:
- Extract wallet addresses from Blokpax listings
- Create Seller records (platform="blokpax", platform_seller_id=wallet_address)
- Set MarketPrice.seller_id on Blokpax listings
- Handle existing BlokpaxListing.seller_address migration

**UOWs**:

- **UOW U3.4.1 — Add seller extraction to Blokpax scraper**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/scraper/blokpax.py`, locate BlokpaxListing/BlokpaxSale parsing, ensure seller_address/buyer_address extracted (already done). Store in dict for Seller creation.
  - Estimate: 1 hour
  - Dependencies: U1.1.1
  - Acceptance Checks: Wallet addresses captured correctly

- **UOW U3.4.2 — Update Blokpax scraper to create Sellers**
  - Type: backend
  - Exact Action: Edit blokpax.py functions that save to MarketPrice (preslab scrapers, etc.) to call get_or_create_seller(platform="blokpax", platform_seller_id=seller_address), set MarketPrice.seller_id.
  - Estimate: 2 hours
  - Dependencies: U3.3.2, U3.4.1
  - Acceptance Checks: Blokpax listings have seller_id, wallet addresses normalized

- **UOW U3.4.3 — Test Blokpax scraper integration**
  - Type: tests
  - Exact Action: Run Blokpax scraper on test storefront, verify Seller records created with platform="blokpax", MarketPrice.seller_id populated.
  - Estimate: 1.5 hours
  - Dependencies: U3.4.2
  - Acceptance Checks: No errors, sellers tracked, wallet addresses unique

---

#### Task T3.5 — Inventory Snapshot Background Job
**Belongs to**: EPIC-3
**Description**: Daily job to snapshot current seller inventory state

**Acceptance Criteria**:
- Scheduled to run daily at 00:00 UTC
- Aggregates SellerInventory into InventorySnapshot
- Computes quantity, avg_price, min_price, max_price per (seller, card, treatment)
- Stores snapshot_date
- Completes in <5 minutes for 10K inventory items

**UOWs**:

- **UOW U3.5.1 — Create snapshot generation function**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/services/inventory_snapshots.py` with async function `generate_daily_snapshot(date: date = today) -> dict` that: 1) Queries SellerInventory grouped by (seller_id, card_id, treatment), 2) Computes aggregates (COUNT, AVG, MIN, MAX), 3) Upserts InventorySnapshot records, 4) Returns stats {snapshots_created, duration}.
  - Estimate: 4 hours
  - Dependencies: U1.4.1 (InventorySnapshot model)
  - Acceptance Checks: Generates snapshots correctly, handles empty inventory, efficient queries

- **UOW U3.5.2 — Add snapshot job to scheduler**
  - Type: backend
  - Exact Action: Edit `/Users/Cody/code_projects/wonder-scraper/app/core/scheduler.py` (or create if doesn't exist) to add scheduled job using APScheduler or similar. Schedule generate_daily_snapshot() at 00:00 UTC daily.
  - Estimate: 2 hours
  - Dependencies: U3.5.1
  - Acceptance Checks: Job runs at scheduled time, logs completion, handles errors

- **UOW U3.5.3 — Create manual snapshot CLI script**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/scripts/generate_snapshot.py` that accepts --date arg (default today), calls generate_daily_snapshot(), prints report. Useful for backfilling historical data.
  - Estimate: 1.5 hours
  - Dependencies: U3.5.1
  - Acceptance Checks: Script works, backfills historical dates, no duplicates

---

### EPIC-4: Admin UI

---

#### Task T4.1 — Seller Management UI
**Belongs to**: EPIC-4
**Description**: Admin page to view, edit, and merge Seller records

**Acceptance Criteria**:
- Table view with pagination (platform, name, listings count, last active)
- Filter by platform, search by name
- Edit seller display name and metadata
- Merge duplicate sellers (combine records)
- View seller's inventory and sales history

**UOWs**:

- **UOW U4.1.1 — Create Sellers list page component**
  - Type: frontend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/frontend/src/routes/admin/sellers/index.tsx` with TanStack Table showing sellers, pagination, platform filter, search input. Fetch data from GET /api/sellers.
  - Estimate: 4 hours
  - Dependencies: U2.1.2 (API exists)
  - Acceptance Checks: Table renders, pagination works, filters apply

- **UOW U4.1.2 — Create Seller detail/edit page**
  - Type: frontend
  - Exact Action: Create frontend/src/routes/admin/sellers/$sellerId.tsx with form to edit display_name, metadata (JSON editor), view inventory table, view sales history. Submit to PUT /api/sellers/{id}.
  - Estimate: 4 hours
  - Dependencies: U4.1.1
  - Acceptance Checks: Form validates, updates seller, shows related data

- **UOW U4.1.3 — Create Seller merge modal**
  - Type: frontend
  - Exact Action: Add "Merge" button to seller list, opens modal to select target seller, confirms merge, calls POST /api/sellers/merge (new endpoint needed - add to backlog). Show warning about data migration.
  - Estimate: 3 hours
  - Dependencies: U4.1.1, requires new backend endpoint (defer or create)
  - Acceptance Checks: Modal works, merge confirmation shown

- **UOW U4.1.4 — Implement backend merge endpoint**
  - Type: backend
  - Exact Action: Add POST /api/sellers/{id}/merge endpoint to sellers.py that accepts target_seller_id, migrates SellerInventory and MarketPrice.seller_id to target, soft-deletes source seller. Wrap in transaction.
  - Estimate: 3 hours
  - Dependencies: U2.1.2
  - Acceptance Checks: Merges sellers, preserves data integrity, rollback on error

---

#### Task T4.2 — SKU Mapping Management UI
**Belongs to**: EPIC-4
**Description**: Admin page to review and manage SKU mappings

**Acceptance Criteria**:
- Table view of SKUMappings (platform, SKU, card name, confidence, verified)
- Filter by platform, verified status, confidence threshold
- Edit mappings (change card_id, update confidence)
- Approve/reject auto-generated mappings
- Bulk approve high-confidence mappings

**UOWs**:

- **UOW U4.2.1 — Create SKU mappings list page**
  - Type: frontend
  - Exact Action: Create frontend/src/routes/admin/sku-mappings/index.tsx with table of SKU mappings, filters (platform, verified, confidence), search by SKU. Fetch from GET /api/sku-mappings.
  - Estimate: 3 hours
  - Dependencies: U2.3.2 (API exists)
  - Acceptance Checks: Table renders, filters work, search functional

- **UOW U4.2.2 — Create SKU mapping edit modal**
  - Type: frontend
  - Exact Action: Add "Edit" action to table, opens modal with form (card_id dropdown, confidence slider, notes textarea, verified checkbox). Submit to PUT /api/sku-mappings/{id}.
  - Estimate: 3 hours
  - Dependencies: U4.2.1
  - Acceptance Checks: Form validates, updates mapping, refreshes table

- **UOW U4.2.3 — Implement bulk approve action**
  - Type: frontend
  - Exact Action: Add checkbox column to table, "Approve Selected" button, calls PUT /api/sku-mappings/bulk-verify (new endpoint) with list of IDs to set verified=True.
  - Estimate: 2 hours
  - Dependencies: U4.2.1, requires backend endpoint
  - Acceptance Checks: Bulk action works, updates multiple mappings

- **UOW U4.2.4 — Create bulk verify endpoint**
  - Type: backend
  - Exact Action: Add PUT /api/sku-mappings/bulk-verify to sku_mappings.py that accepts list of mapping IDs, updates verified=True, returns count of updated records.
  - Estimate: 2 hours
  - Dependencies: U2.3.2
  - Acceptance Checks: Updates multiple mappings, validates IDs exist

---

#### Task T4.3 — CSV Upload UI
**Belongs to**: EPIC-4
**Description**: Admin page to upload CSV files with preview and validation

**Acceptance Criteria**:
- File upload component (drag-and-drop or browse)
- Platform selector (eBay, Blokpax, ShootStrayt, etc.)
- Preview first 10 rows with validation feedback
- Submit button to trigger import
- Progress indicator and import report

**UOWs**:

- **UOW U4.3.1 — Create CSV upload page**
  - Type: frontend
  - Exact Action: Create frontend/src/routes/admin/import/csv.tsx with file upload input, platform dropdown, "Preview" button. Uses FileReader API to parse CSV client-side, displays first 10 rows in table.
  - Estimate: 3 hours
  - Dependencies: None
  - Acceptance Checks: Upload works, preview shows data, platform selected

- **UOW U4.3.2 — Implement CSV validation preview**
  - Type: frontend
  - Exact Action: Add client-side validation (check columns, data types), highlight errors (missing SKU, invalid price), show validation summary (X errors found).
  - Estimate: 3 hours
  - Dependencies: U4.3.1
  - Acceptance Checks: Detects errors, highlights rows, clear error messages

- **UOW U4.3.3 — Create CSV upload API endpoint**
  - Type: backend
  - Exact Action: Add POST /api/import/csv to new router, accepts multipart form with file and platform param, saves file temporarily, calls csv_importer.import_csv(), returns import report (success/failure counts, errors).
  - Estimate: 3 hours
  - Dependencies: U3.1.3 (CSV importer exists)
  - Acceptance Checks: Endpoint accepts file, processes CSV, returns report

- **UOW U4.3.4 — Implement import submission and progress**
  - Type: frontend
  - Exact Action: Add "Import" button to CSV upload page, submits file to POST /api/import/csv, shows loading spinner, displays import report on completion (success count, error details).
  - Estimate: 2 hours
  - Dependencies: U4.3.3
  - Acceptance Checks: Import triggers, progress shown, report displayed

---

#### Task T4.4 — Inventory Snapshot Viewer
**Belongs to**: EPIC-4
**Description**: Admin page to view historical inventory snapshots

**Acceptance Criteria**:
- Filter by seller, card, date range
- Chart showing inventory quantity over time
- Table view of snapshot details
- Export to CSV option

**UOWs**:

- **UOW U4.4.1 — Create snapshot viewer page**
  - Type: frontend
  - Exact Action: Create frontend/src/routes/admin/inventory/snapshots.tsx with filters (seller dropdown, card search, date range picker), "Load" button to fetch data from GET /api/inventory/snapshots.
  - Estimate: 3 hours
  - Dependencies: U2.4.2 (API exists)
  - Acceptance Checks: Filters work, data loads, handles empty results

- **UOW U4.4.2 — Add time-series chart component**
  - Type: frontend
  - Exact Action: Add Recharts (or similar) line chart to snapshot viewer showing quantity over snapshot_date, separate lines per treatment if multiple. Use data from API response.
  - Estimate: 3 hours
  - Dependencies: U4.4.1
  - Acceptance Checks: Chart renders, interactive, tooltips work

- **UOW U4.4.3 — Add snapshot details table**
  - Type: frontend
  - Exact Action: Add table below chart showing snapshot records (date, seller, card, treatment, quantity, avg_price), pagination, sortable columns.
  - Estimate: 2 hours
  - Dependencies: U4.4.1
  - Acceptance Checks: Table displays data, pagination works, sorting functional

---

### EPIC-5: Analytics & Observability

---

#### Task T5.1 — Seller Analytics API
**Belongs to**: EPIC-5
**Description**: Endpoints for seller performance metrics

**Acceptance Criteria**:
- GET /api/sellers/{id}/analytics (inventory size, 30d sales volume, market share)
- GET /api/analytics/supply-diversity (sellers per card, Herfindahl index)
- GET /api/analytics/inventory-velocity (avg days to sell)
- Response time <500ms for most queries

**UOWs**:

- **UOW U5.1.1 — Implement GET /sellers/{id}/analytics**
  - Type: backend
  - Exact Action: Add endpoint to sellers.py that queries: 1) Current inventory size (SUM quantity from SellerInventory), 2) Last 30d sales volume (COUNT sold MarketPrice), 3) Market share (seller's sales / total sales), 4) Avg listing price. Cache results for 1 hour.
  - Estimate: 4 hours
  - Dependencies: U2.1.2, sufficient historical data
  - Acceptance Checks: Returns accurate metrics, <500ms response, caching works

- **UOW U5.1.2 — Implement supply diversity endpoint**
  - Type: backend
  - Exact Action: Create `/Users/Cody/code_projects/wonder-scraper/app/api/analytics.py` with GET /analytics/supply-diversity accepting card_id param, returns: seller_count, Herfindahl-Hirschman Index (sum of squared market shares), top sellers. Use SellerInventory + MarketPrice.
  - Estimate: 4 hours
  - Dependencies: U2.1.2
  - Acceptance Checks: Calculations correct, efficient queries, handles edge cases

- **UOW U5.1.3 — Implement inventory velocity endpoint**
  - Type: backend
  - Exact Action: Add GET /analytics/inventory-velocity to analytics.py, calculates avg time from MarketPrice.listed_at to sold_date for active->sold transitions, group by card_id, seller_id, treatment. Returns median days to sell.
  - Estimate: 4 hours
  - Dependencies: U2.1.2
  - Acceptance Checks: Calculation accurate, excludes outliers (>180 days), performant

---

#### Task T5.2 — Data Quality Dashboard
**Belongs to**: EPIC-5
**Description**: Admin UI showing data quality metrics

**Acceptance Criteria**:
- % of MarketPrice with seller_id populated
- % of SKUs mapped vs unmapped
- Recent import job statuses
- Error logs for failed imports
- Target: <5% unmapped SKUs, >95% seller_id coverage

**UOWs**:

- **UOW U5.2.1 — Create data quality metrics endpoint**
  - Type: backend
  - Exact Action: Add GET /api/admin/data-quality to admin.py (or analytics.py) that queries: 1) MarketPrice seller_id coverage, 2) SKUMapping verified vs unverified counts, 3) Recent import job logs (from new ImportLog table - add to models), 4) Unmapped SKU sample.
  - Estimate: 3 hours
  - Dependencies: U2.1.2
  - Acceptance Checks: Metrics accurate, response <1s

- **UOW U5.2.2 — Create ImportLog model**
  - Type: backend
  - Exact Action: Add ImportLog model to seller.py or new models file with fields: id, import_type (csv, api, scraper), platform, status (success, partial, failed), total_rows, success_count, error_count, errors (JSON), started_at, completed_at.
  - Estimate: 2 hours
  - Dependencies: U1.1.1
  - Acceptance Checks: Model validates, migration created

- **UOW U5.2.3 — Update ETL jobs to log to ImportLog**
  - Type: backend
  - Exact Action: Edit csv_importer.py, shootstrayt import script, scraper updates to create ImportLog records on start, update on completion with stats and errors.
  - Estimate: 2 hours
  - Dependencies: U5.2.2
  - Acceptance Checks: Jobs create logs, errors captured, timestamps accurate

- **UOW U5.2.4 — Create data quality dashboard page**
  - Type: frontend
  - Exact Action: Create frontend/src/routes/admin/data-quality.tsx with cards showing: seller_id coverage %, SKU mapping %, recent import jobs table (status, counts, timestamp), unmapped SKUs list. Fetch from GET /api/admin/data-quality.
  - Estimate: 4 hours
  - Dependencies: U5.2.1
  - Acceptance Checks: Dashboard displays metrics, updates on refresh, clear visualizations

---

#### Task T5.3 — ETL Monitoring & Logging
**Belongs to**: EPIC-5
**Description**: Centralized logging and monitoring for data pipelines

**Acceptance Criteria**:
- All ETL jobs log start/end/errors to structured logger
- Logs queryable via admin UI
- Alerts on job failures (email/Discord webhook)
- Logs retained for 30 days

**UOWs**:

- **UOW U5.3.1 — Implement structured logging in ETL jobs**
  - Type: backend
  - Exact Action: Edit csv_importer.py, shootstrayt scripts, scraper updates to use Python logging module with JSON formatter (structlog or similar). Log: job_id, timestamp, level, message, context (platform, counts, errors).
  - Estimate: 3 hours
  - Dependencies: None
  - Acceptance Checks: Logs structured, parseable, includes context

- **UOW U5.3.2 — Create job logs viewer endpoint**
  - Type: backend
  - Exact Action: Add GET /api/admin/job-logs to admin.py that queries ImportLog table, supports filters (status, platform, date range), pagination, returns JSON list.
  - Estimate: 2 hours
  - Dependencies: U5.2.2
  - Acceptance Checks: Endpoint returns logs, filters work, paginated

- **UOW U5.3.3 — Add job logs viewer to admin UI**
  - Type: frontend
  - Exact Action: Create frontend/src/routes/admin/logs.tsx with table of job logs, filters (status, platform, date), expandable rows to show error details. Fetch from GET /api/admin/job-logs.
  - Estimate: 3 hours
  - Dependencies: U5.3.2
  - Acceptance Checks: Logs display, filters work, error details visible

- **UOW U5.3.4 — Implement failure alerting**
  - Type: backend
  - Exact Action: Edit ETL jobs to send Discord webhook notification (using existing discord_bot/logger.py) on job failure. Include job type, error summary, timestamp. Optional: email alerts via email service.
  - Estimate: 2 hours
  - Dependencies: U5.3.1
  - Acceptance Checks: Alerts sent on failure, message clear, no false positives

---

## E. Delivery & Risk Plan

### Sprint Mapping

#### Sprint 1 (Phase 1 - Foundation)
**Theme**: Database architecture and models
**Phase/Epic**: Phase 1 / EPIC-1
**Must-Have UOWs**:
- U1.1.1 - U1.1.2 (Seller model)
- U1.2.1 - U1.2.2 (SellerInventory model)
- U1.3.1 - U1.3.2 (SKUMapping model)
- U1.4.1 - U1.4.2 (InventorySnapshot model)
- U1.5.1 - U1.5.2 (Update MarketPrice)
- U1.6.1 - U1.6.2 (Alembic migration)

**Nice-to-Have**: U1.8.1 (Unit tests - can spill to Sprint 2)
**Demo Checkpoint**: Show ERD, run migration on staging, query new tables

---

#### Sprint 2 (Phase 1 - Data Migration)
**Theme**: Backfill historical seller data
**Phase/Epic**: Phase 1 / EPIC-1
**Must-Have UOWs**:
- U1.7.1 - U1.7.3 (Migration script)
- U1.8.1 (Unit tests)

**Nice-to-Have**: Additional migration testing, edge case handling
**Demo Checkpoint**: Show seller_id coverage metrics, sample merged sellers

---

#### Sprint 3 (Phase 2 - API Layer)
**Theme**: RESTful APIs for seller management
**Phase/Epic**: Phase 2 / EPIC-2
**Must-Have UOWs**:
- U2.1.1 - U2.1.4 (Seller CRUD)
- U2.2.1 - U2.2.4 (Inventory endpoints)
- U2.3.1 - U2.3.4 (SKU mappings)
- U2.4.1 - U2.4.2 (Snapshots)

**Nice-to-Have**: U2.5.1 - U2.5.3 (Tests - can parallelize)
**Demo Checkpoint**: Postman collection demo, Swagger docs review

---

#### Sprint 4 (Phase 3 - ETL Part 1)
**Theme**: CSV import and scraper updates
**Phase/Epic**: Phase 3 / EPIC-3
**Must-Have UOWs**:
- U3.1.1 - U3.1.4 (CSV import)
- U3.3.1 - U3.3.4 (eBay scraper)
- U3.4.1 - U3.4.3 (Blokpax scraper)

**Nice-to-Have**: U3.5.1 - U3.5.3 (Snapshot job - can defer)
**Demo Checkpoint**: Import sample CSV, run scrapers, show seller creation

---

#### Sprint 5 (Phase 3 - ETL Part 2)
**Theme**: ShootStrayt integration and automation
**Phase/Epic**: Phase 3 / EPIC-3
**Must-Have UOWs**:
- U3.2.1 - U3.2.4 (ShootStrayt integration)
- U3.5.1 - U3.5.3 (Snapshot job)

**Nice-to-Have**: Additional SKU parsers for future platforms
**Demo Checkpoint**: ShootStrayt inventory imported, snapshots generated

---

#### Sprint 6 (Phase 4 - Admin UI)
**Theme**: Admin management interfaces
**Phase/Epic**: Phase 4 / EPIC-4
**Must-Have UOWs**:
- U4.1.1 - U4.1.4 (Seller management)
- U4.2.1 - U4.2.4 (SKU mappings)
- U4.3.1 - U4.3.4 (CSV upload)

**Nice-to-Have**: U4.4.1 - U4.4.3 (Snapshot viewer - defer if tight)
**Demo Checkpoint**: Admin walkthrough, CSV upload demo, seller merge

---

#### Sprint 7 (Phase 5 - Analytics)
**Theme**: Insights and observability
**Phase/Epic**: Phase 5 / EPIC-5
**Must-Have UOWs**:
- U5.1.1 - U5.1.3 (Analytics endpoints)
- U5.2.1 - U5.2.4 (Data quality dashboard)
- U5.3.1 - U5.3.4 (Logging & monitoring)

**Nice-to-Have**: Advanced analytics, ML features (future)
**Demo Checkpoint**: Analytics dashboard demo, data quality review, monitoring setup

---

### Critical Path

**Blocking Dependencies**:
1. **Database Models (Sprint 1)** → Everything else (no models = no API/UI)
2. **API Layer (Sprint 3)** → Admin UI (Sprint 6)
3. **CSV Importer (Sprint 4)** → CSV Upload UI (Sprint 6)
4. **Historical Data (Sprint 4-5)** → Analytics (Sprint 7)

**Non-Blocking Parallel Work**:
- Unit tests (can run alongside implementation)
- Documentation (continuous)
- ShootStrayt integration (independent from eBay/Blokpax)
- Admin UI components (can mock API initially)

**Critical Path Sequence**:
```
Sprint 1 (Models) → Sprint 2 (Migration) → Sprint 3 (API) → Sprint 4 (ETL) → Sprint 6 (UI) → Sprint 7 (Analytics)
                                                        ↘ Sprint 5 (ShootStrayt) ↗
```

---

### Risks & Hidden Work

#### Architectural Risks

| Risk | Why It Matters | Phase/Epic | Impact if Ignored |
|------|---------------|-----------|------------------|
| **Seller identity conflicts** | Same seller on multiple platforms with different names | EPIC-1 | High - duplicate sellers, fragmented data |
| **SKU format variations** | Platforms may change SKU formats over time | EPIC-3 | Medium - broken mappings, manual fixes |
| **Database performance** | Large SellerInventory table (1M+ rows) | EPIC-1 | High - slow queries, poor UX |
| **Migration rollback** | Complex data migration may fail in production | EPIC-1 | High - data loss, downtime |

**Mitigation**:
- Add `external_identifiers` JSON field to Seller for cross-platform linking
- Version SKU parsers, store parser version in SKUMapping
- Add composite indexes, consider partitioning InventorySnapshot by date
- Test migration on production snapshot, have rollback plan ready

---

#### Data Model Risks

| Risk | Why It Matters | Phase/Epic | Impact if Ignored |
|------|---------------|-----------|------------------|
| **NULL seller_id proliferation** | If migration incomplete, analytics will be skewed | EPIC-1 | Medium - inaccurate metrics |
| **SKU mapping ambiguity** | One SKU maps to multiple cards (variant treatments) | EPIC-3 | Medium - wrong inventory counts |
| **Snapshot data retention** | Daily snapshots grow unbounded | EPIC-3 | Medium - storage costs, slow queries |
| **Inventory staleness** | No timestamp on inventory means don't know if current | EPIC-1 | Low - minor accuracy issues |

**Mitigation**:
- Monitor seller_id coverage, alert if <90%
- Add (platform, sku, treatment) unique constraint to SKUMapping
- Implement snapshot retention policy (keep 90 days, aggregate older)
- SellerInventory.updated_at tracks freshness, add "last_verified" field

---

#### External API/Integration Risks

| Risk | Why It Matters | Phase/Epic | Impact if Ignored |
|------|---------------|-----------|------------------|
| **ShootStrayt API unavailable** | May need manual CSV workflow | EPIC-3 | Low - workaround exists |
| **eBay rate limiting** | Scraper may hit limits creating Sellers | EPIC-3 | Medium - incomplete data |
| **Blokpax wallet format changes** | Blockchain upgrades could change address format | EPIC-3 | Low - unlikely in short term |
| **CSV schema variations** | Different sellers provide different formats | EPIC-3 | Medium - import failures |

**Mitigation**:
- Make API integration optional, CSV as fallback
- Implement exponential backoff, cache Seller lookups
- Store raw wallet addresses, normalize on query
- Schema validator with clear error messages, support multiple formats

---

#### Migration Risks

| Risk | Why It Matters | Phase/Epic | Impact if Ignored |
|------|---------------|-----------|------------------|
| **Duplicate seller detection** | Fuzzy matching may merge different sellers | EPIC-1 | High - data corruption |
| **NULL seller_name handling** | Some MarketPrice records lack seller info | EPIC-1 | Low - expected for some platforms |
| **Performance during migration** | Backfill script may lock tables | EPIC-1 | Medium - production slowdown |
| **Incomplete backfill** | Script crashes mid-run | EPIC-1 | Medium - partial data state |

**Mitigation**:
- Conservative matching (high threshold), manual review for edge cases
- Skip NULL seller_name, log count for visibility
- Run migration during low-traffic window, batch updates (1000 rows/txn)
- Idempotent script (can re-run), transaction per batch

---

#### DevOps/CI Risks

| Risk | Why It Matters | Phase/Epic | Impact if Ignored |
|------|---------------|-----------|------------------|
| **Missing monitoring** | ETL jobs fail silently | EPIC-5 | High - stale data, broken integrations |
| **No alerting on errors** | Import failures go unnoticed | EPIC-5 | High - data gaps |
| **Lack of testing in CI** | Model changes break existing code | EPIC-1 | Medium - production bugs |
| **No API versioning** | Breaking changes impact frontend | EPIC-2 | Low - internal API, low risk |

**Mitigation**:
- EPIC-5 includes logging/monitoring as core feature (not nice-to-have)
- Add Discord alerts on ETL failures (using existing webhook)
- Add model tests to CI, require >80% coverage
- Use API versioning best practices if needed (v1, v2 paths)

---

#### Invisible Work (Often Forgotten)

| Work Item | Why It's Needed | Phase/Epic | Estimate |
|-----------|----------------|-----------|---------|
| **Error handling in ETL** | Gracefully handle malformed CSV, API errors | EPIC-3 | 4 hours |
| **Logging throughout** | Debug production issues | EPIC-3, EPIC-5 | 6 hours |
| **Database indexes** | Query performance for analytics | EPIC-1 | 2 hours |
| **API pagination** | Handle large result sets | EPIC-2 | 3 hours |
| **Migration rollback plan** | Recover from failed migration | EPIC-1 | 4 hours |
| **Feature flags** | Gradual rollout of new seller tracking | EPIC-1 | 3 hours |
| **Data validation** | Prevent bad data from entering DB | EPIC-2, EPIC-3 | 5 hours |
| **API rate limiting** | Prevent abuse of endpoints | EPIC-2 | 2 hours |
| **Caching strategies** | Reduce DB load for analytics | EPIC-5 | 4 hours |
| **Documentation** | API docs, runbooks, ERD diagrams | All epics | 12 hours |
| **Security audit** | Ensure no SQL injection, auth bypass | EPIC-2 | 3 hours |

**Total Invisible Work**: ~48 hours (~1 sprint) - Factor into timeline

---

### Tech Debt Decisions (Intentional)

**Accept for MVP** (address post-launch):
1. **Manual seller merging** - No automatic duplicate detection (too complex for v1)
2. **Single-threaded imports** - CSV import not parallelized (sufficient for <10K rows)
3. **Basic SKU fuzzy matching** - No ML-based matching (90% accuracy acceptable)
4. **No real-time inventory** - Daily snapshots sufficient (not a trading platform)
5. **Limited platform support** - Only eBay, Blokpax, ShootStrayt (others as needed)

**Address in v1** (required for production):
1. **Seller_id backfill** - Must achieve >95% coverage before launch
2. **API authentication** - Required for write operations
3. **Data quality monitoring** - Needed to catch issues early
4. **Migration testing** - Must test on production snapshot
5. **Error logging** - Essential for debugging ETL issues

**Future enhancements** (post-v1):
- Seller reputation scoring
- Predictive inventory analytics (ML)
- Real-time inventory webhooks
- Automatic SKU conflict resolution
- Multi-seller price comparison tools
- Public seller profiles (if desired)

---

### Recommended Sequencing

**DO FIRST** (foundational, high-risk):
1. Database models + migration (Sprint 1)
2. Data migration script (Sprint 2)
3. API layer (Sprint 3)

**DO NEXT** (enables user value):
4. CSV import (Sprint 4)
5. Scraper updates (Sprint 4-5)
6. Admin UI (Sprint 6)

**DO LAST** (polish, observability):
7. Analytics endpoints (Sprint 7)
8. Monitoring dashboards (Sprint 7)

**CAN DEFER** (nice-to-have):
- ShootStrayt integration (if API not ready)
- Snapshot viewer UI (admin can query DB directly)
- Advanced analytics (initial metrics sufficient)

**PARALLELIZATION OPPORTUNITIES**:
- Tests can run alongside implementation (different dev)
- Documentation can be written continuously
- Frontend can mock API and develop in parallel (Sprint 5-6)
- ShootStrayt and eBay/Blokpax updates are independent

---

## Appendix: Open Questions Requiring Answers

**Before Sprint 1**:
- [ ] Q1: ShootStrayt API credentials and documentation available?
- [ ] Q2: Confirm SKU format variations across platforms
- [ ] Q6: Backfill historical seller data or start fresh?

**Before Sprint 3**:
- [ ] Q3: Inventory update frequency requirements (daily vs hourly)
- [ ] Q7: Admin UI priority (needed for MVP or API-only acceptable?)

**Before Sprint 4**:
- [ ] Q4: Seller identity merging rules (manual vs automatic)
- [ ] Q5: CSV import schema finalized (sample files reviewed)

**Nice-to-have answers** (can proceed without):
- Seller reputation scoring approach
- Real-time vs batch inventory updates
- Public seller profiles requirements

---

## Success Metrics

**Technical Metrics**:
- Seller_id coverage: >95% of MarketPrice records
- SKU mapping accuracy: >90% auto-mapped correctly
- API response time: <500ms p95
- ETL job success rate: >98%
- Data quality: <5% unmapped SKUs

**Business Metrics**:
- Seller count tracked: 500+ unique sellers
- Inventory items tracked: 10,000+ SKUs
- Import volume: 1,000+ rows/day
- Admin usage: 10+ CSV uploads/week

**User Experience**:
- CSV import: <30 seconds for 1000 rows
- Admin UI load time: <2 seconds
- Zero data loss during migration
- <1 day downtime for major updates

---

**Document Version**: 1.0
**Last Updated**: 2025-12-08
**Next Review**: After Q&A session with team
