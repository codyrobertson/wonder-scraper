# EPIC-9: Analytics & Observability

**Status**: Planned
**Sprint**: 7
**Priority**: Medium
**Dependencies**: EPIC-8 (Admin UI), 2+ weeks of historical data

---

## Objective

Surface seller and inventory insights through API and dashboards, plus monitoring for ETL jobs.

## User Impact

Users can make informed decisions based on supply metrics and seller performance.

## Tech Scope

- Analytics endpoints with aggregation queries
- Data quality dashboards
- Logging and monitoring for ETL jobs
- Discord alerting for failures

---

## Done-When Criteria

- [ ] Seller analytics API returns metrics in <500ms
- [ ] Data quality dashboard shows <5% error rate
- [ ] ETL job logs queryable via admin UI
- [ ] Alerts sent to Discord on job failures
- [ ] Supply diversity metrics match manual calculations

---

## Analytics Endpoints

### Seller Analytics
```
GET /api/sellers/{id}/analytics
```
Returns:
- `inventory_size`: Current total quantity
- `sales_volume_30d`: Sales count in last 30 days
- `market_share`: Seller's sales / total sales
- `avg_listing_price`: Average price of active listings

### Supply Diversity
```
GET /api/analytics/supply-diversity?card_id={id}
```
Returns:
- `seller_count`: Number of unique sellers
- `hhi_index`: Herfindahl-Hirschman Index (market concentration)
- `top_sellers`: List of top 5 sellers by inventory

### Inventory Velocity
```
GET /api/analytics/inventory-velocity?card_id={id}
```
Returns:
- `median_days_to_sell`: Median time from listed to sold
- `velocity_by_treatment`: Breakdown by treatment type
- `trend`: Velocity trend (faster/slower vs last period)

---

## Data Quality Metrics

### Dashboard Metrics
- **Seller Coverage**: % of MarketPrice with seller_id populated
- **SKU Mapping Rate**: % of SKUs mapped vs unmapped
- **Import Success Rate**: % of successful import jobs
- **Unmapped SKU Sample**: List of most common unmapped SKUs

### Targets
- Seller_id coverage: >95%
- SKU mapping rate: >90%
- Import success rate: >98%
- Unmapped SKUs: <5%

---

## Tasks

### T5.1 — Seller Analytics API

**UOWs**:
- U5.1.1: Implement GET /sellers/{id}/analytics (4h)
- U5.1.2: Implement supply diversity endpoint (4h)
- U5.1.3: Implement inventory velocity endpoint (4h)

### T5.2 — Data Quality Dashboard

**UOWs**:
- U5.2.1: Create data quality metrics endpoint (3h)
- U5.2.2: Create ImportLog model (2h)
- U5.2.3: Update ETL jobs to log to ImportLog (2h)
- U5.2.4: Create data quality dashboard page (4h)

### T5.3 — ETL Monitoring & Logging

**UOWs**:
- U5.3.1: Implement structured logging in ETL jobs (3h)
- U5.3.2: Create job logs viewer endpoint (2h)
- U5.3.3: Add job logs viewer to admin UI (3h)
- U5.3.4: Implement failure alerting (Discord webhook) (2h)

---

## ImportLog Model

```python
class ImportLog(SQLModel, table=True):
    id: int  # PK
    import_type: str  # csv, api, scraper
    platform: str  # ebay, blokpax, shootstrayt
    status: str  # pending, running, success, partial, failed
    total_rows: Optional[int]
    success_count: Optional[int]
    error_count: Optional[int]
    errors: Optional[dict]  # JSON: [{row: 5, error: "Invalid SKU"}, ...]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
```

---

## Alerting

### Discord Webhook on Failure
When an ETL job fails, send to Discord:
```
🚨 ETL Job Failed
Type: csv_import
Platform: shootstrayt
Error: SKU validation failed for 15 rows
Time: 2025-12-09 03:00 UTC
```

### Alert Conditions
- Import job fails with >10% error rate
- Scraper fails to complete
- Snapshot job times out (>5 minutes)
- Any unhandled exception in ETL

---

## Required Documentation

- `/docs/ANALYTICS.md` - Metric definitions and calculation methods
- `/docs/MONITORING.md` - Dashboard access, alerting setup
