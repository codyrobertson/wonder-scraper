# Phase 5: Multi-Source Seller & Inventory Integration

**Status**: Active
**Priority**: High
**Sprints**: 7 (Sprint 1-7)
**Created**: 2025-12-08

---

## Goals

### Product Goals
- **Unified Seller Tracking**: Track sellers across multiple platforms (eBay, Blokpax, ShootStrayt)
- **Inventory Management**: Monitor stock levels per seller, per card, per treatment
- **SKU Mapping System**: Map external SKUs to internal Card IDs
- **Multi-Source ETL**: Support CSV imports, scraper-based ingestion, and future API integrations
- **Supply Analytics**: Enable seller concentration, supply diversity, and inventory velocity insights

### Technical Goals
- Normalize seller data from string fields to dedicated Seller model
- Extensible architecture for adding new platforms
- Backward compatibility during migration from `seller_name` strings to Seller FK
- Audit trail for inventory changes and SKU mappings
- Performance at scale (100K+ listings, 1K+ sellers)

---

## Epics

| Epic | Name | Sprint | Status |
|------|------|--------|--------|
| EPIC-5 | Database Schema & Models | 1-2 | Planned |
| EPIC-6 | Seller Management API | 3 | Planned |
| EPIC-7 | ETL & Data Ingestion | 4-5 | Planned |
| EPIC-8 | Admin UI | 6 | Planned |
| EPIC-9 | Analytics & Observability | 7 | Planned |

---

## Key Decisions

### Confirmed
- **ShootStrayt**: Will use scraping approach (no API needed for now)
- **SKU Format**: ShootStrayt uses `{PRODUCT}-{SET}-{NUMBER}-{RARITY}-{TREATMENT}`
- **Inventory Updates**: Daily snapshots are sufficient (not real-time)

### Recommendations (To Be Confirmed)
1. **Backfill Strategy**: YES - Migrate existing `seller_name` data to new Seller table
2. **CSV Schema**: Define standard format with columns: platform, seller_id, sku, quantity, price, notes
3. **Admin UI**: API-first with basic admin UI for MVP (defer complex UI features)

---

## Critical Path

```
Sprint 1-2 (Models) → Sprint 3 (API) → Sprint 4-5 (ETL) → Sprint 6 (UI) → Sprint 7 (Analytics)
```

**Blocking Dependencies**:
1. Database Models (Sprint 1-2) → Everything else
2. API Layer (Sprint 3) → Admin UI (Sprint 6)
3. CSV Importer (Sprint 4) → CSV Upload UI (Sprint 6)
4. Historical Data (Sprint 4-5) → Analytics (Sprint 7)

---

## Success Metrics

**Technical**:
- Seller_id coverage: >95% of MarketPrice records
- SKU mapping accuracy: >90% auto-mapped correctly
- API response time: <500ms p95
- ETL job success rate: >98%

**Business**:
- Seller count tracked: 500+ unique sellers
- Inventory items tracked: 10,000+ SKUs
- Import volume: 1,000+ rows/day

---

## Related Documents

- [EPIC-5: Database Schema](./EPIC-5-Database-Schema/README.md)
- [EPIC-6: Seller Management API](./EPIC-6-Seller-Management-API/README.md)
- [EPIC-7: ETL & Data Ingestion](./EPIC-7-ETL-Data-Ingestion/README.md)
- [EPIC-8: Admin UI](./EPIC-8-Admin-UI/README.md)
- [EPIC-9: Analytics & Observability](./EPIC-9-Analytics-Observability/README.md)
