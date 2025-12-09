# EPIC-8: Admin UI

**Status**: Planned
**Sprint**: 6
**Priority**: Medium
**Dependencies**: EPIC-7 (ETL Pipelines)

---

## Objective

Build admin interfaces for managing sellers, SKU mappings, and inventory data.

## User Impact

Admins can visually manage integrations without API calls.

## Tech Scope

- React components with TanStack Router
- Forms with validation
- Tables with pagination/sorting
- File upload handling

---

## Done-When Criteria

- [ ] Admin can upload CSV and see preview before import
- [ ] Admin can manually create/edit SKU mappings
- [ ] Admin can merge duplicate seller profiles
- [ ] Admin can view inventory snapshots by seller/card
- [ ] All forms have proper validation and error messages

---

## Pages

### /admin/sellers
Seller management table with:
- Pagination, filters (platform), search
- Edit seller display name and metadata
- View seller inventory and sales history
- Merge duplicate sellers

### /admin/sku-mappings
SKU mapping management with:
- Filter by platform, verified status, confidence
- Edit mappings (change card, update confidence)
- Approve/reject auto-generated mappings
- Bulk approve high-confidence mappings

### /admin/import/csv
CSV upload page with:
- File upload (drag-and-drop)
- Platform selector
- Preview first 10 rows with validation
- Import button with progress indicator

### /admin/inventory/snapshots
Snapshot viewer with:
- Filter by seller, card, date range
- Time-series chart (quantity over time)
- Table view of snapshot details

---

## Tasks

### T4.1 — Seller Management UI

**UOWs**:
- U4.1.1: Create Sellers list page component (4h)
- U4.1.2: Create Seller detail/edit page (4h)
- U4.1.3: Create Seller merge modal (3h)
- U4.1.4: Implement backend merge endpoint (3h)

### T4.2 — SKU Mapping Management UI

**UOWs**:
- U4.2.1: Create SKU mappings list page (3h)
- U4.2.2: Create SKU mapping edit modal (3h)
- U4.2.3: Implement bulk approve action (2h)
- U4.2.4: Create bulk verify endpoint (2h)

### T4.3 — CSV Upload UI

**UOWs**:
- U4.3.1: Create CSV upload page (3h)
- U4.3.2: Implement CSV validation preview (3h)
- U4.3.3: Create CSV upload API endpoint (3h)
- U4.3.4: Implement import submission and progress (2h)

### T4.4 — Inventory Snapshot Viewer

**UOWs**:
- U4.4.1: Create snapshot viewer page (3h)
- U4.4.2: Add time-series chart component (3h)
- U4.4.3: Add snapshot details table (2h)

---

## Component Structure

```
frontend/src/routes/admin/
├── sellers/
│   ├── index.tsx        # Sellers list
│   └── $sellerId.tsx    # Seller detail/edit
├── sku-mappings/
│   └── index.tsx        # SKU mappings list
├── import/
│   └── csv.tsx          # CSV upload
└── inventory/
    └── snapshots.tsx    # Snapshot viewer
```

---

## MVP Scope vs Deferred

### MVP (Sprint 6)
- Seller list with basic filters
- SKU mapping list with verify action
- CSV upload with preview
- Basic validation and error handling

### Deferred (Post-MVP)
- Advanced seller merge UI
- Snapshot time-series charts (defer to Sprint 7)
- Bulk actions beyond verify
- Export functionality

---

## Required Documentation

- `/docs/ADMIN_UI.md` - User guide for admin features
- `/docs/UI_COMPONENTS.md` - Reusable component documentation
