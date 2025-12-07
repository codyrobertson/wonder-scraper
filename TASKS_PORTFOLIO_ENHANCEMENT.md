# Portfolio Enhancement Epic

## Overview
Transform portfolio from quantity-based tracking to individual card tracking with treatment, source, grading, and accurate market pricing.

## Current → New Model

```
OLD: portfolio_item { card_id, quantity, purchase_price }
NEW: portfolio_card { card_id, treatment, source, purchase_price, purchase_date, grading }
     (one row per physical card)
```

## Phases

| Phase | Focus | Sprints |
|-------|-------|---------|
| 1 | Database Schema & Migration | 1 |
| 2 | Treatment-Aware Pricing & Core UI | 1 |
| 3 | Multi-Card Entry & UX Polish | 1.5 |
| 4 | Bulk Actions & Advanced Features | 1 |

---

## Phase 1: Foundation & Data Model

### EPIC-1: Database Schema & Migration

| Task | Description | Status |
|------|-------------|--------|
| T1.1 | Define `portfolio_cards` SQLModel | pending |
| T1.2 | Create Alembic migration | pending |
| T1.3 | Write data backfill script (quantity → N rows) | pending |
| T1.4 | Validate migration on test data | pending |

**New Model Fields:**
- `id` - Primary key
- `user_id` - Foreign key to users
- `card_id` - Foreign key to cards
- `treatment` - Paper, Foil, Formless, Serialized, Promo (from DB)
- `source` - eBay, Blokpax, TCGPlayer, LGS, Trade, PackPull, Other
- `purchase_price` - Decimal
- `purchase_date` - Date
- `grading` - Optional (e.g., "PSA 10", "BGS 9.5", null for raw)
- `created_at`, `updated_at` - Timestamps

---

### EPIC-2: Backend API for Individual Card CRUD

| Task | Description | Status |
|------|-------------|--------|
| T2.1 | POST /api/portfolio/cards - Add single card | pending |
| T2.2 | GET /api/portfolio/cards - List with filters | pending |
| T2.3 | PATCH /api/portfolio/cards/{id} - Update card | pending |
| T2.4 | DELETE /api/portfolio/cards/{id} - Remove card | pending |
| T2.5 | Write integration tests | pending |

**Validation Rules:**
- `card_id` must exist in cards table
- `treatment` must exist in DB (not free text)
- `purchase_price` > 0
- `purchase_date` not in future
- `grading` format: "PSA 10", "BGS 9.5", "CGC 9"

---

### EPIC-3: Backward-Compatible Legacy API

| Task | Description | Status |
|------|-------------|--------|
| T3.1 | GET /api/portfolio (aggregated from new table) | pending |
| T3.2 | POST /api/portfolio (explode quantity → N cards) | pending |

---

## Phase 2: Treatment-Aware Pricing & Core UI

### EPIC-4: Treatment-Specific Market Pricing

| Task | Description | Status |
|------|-------------|--------|
| T4.1 | Add treatment filter to price query | pending |
| T4.2 | GET /api/cards/{id}/price?treatment=X | pending |
| T4.3 | Add P/L calculation to portfolio response | pending |

**P/L Calculation:**
```
profit_loss = market_price - purchase_price
profit_loss_pct = (market_price / purchase_price - 1) * 100
```

---

### EPIC-5: Basic Portfolio UI with Individual Cards

| Task | Description | Status |
|------|-------------|--------|
| T5.1 | Update table columns (treatment badge, P/L) | pending |
| T5.2 | Implement group/ungroup toggle | pending |
| T5.3 | Add delete card action | pending |

**Table Columns:**
- Card Name (link to detail)
- Treatment Badge (color-coded)
- Source
- Purchase Price
- Purchase Date
- Market Price
- P/L ($)
- P/L (%)
- Actions (delete)

**Treatment Badge Colors:**
- Paper: gray
- Foil: gold
- Formless: blue
- Serialized: red
- Promo: purple

---

### EPIC-6: Single-Card Entry Form

| Task | Description | Status |
|------|-------------|--------|
| T6.1 | Create add card modal component | pending |
| T6.2 | Implement form validation with Zod | pending |
| T6.3 | Wire form to POST API | pending |

**Form Fields:**
- Card (search combobox)
- Treatment (dropdown from DB)
- Source (dropdown enum)
- Purchase Price (number)
- Purchase Date (date picker)
- Graded? (checkbox) → Company + Grade inputs

---

## Phase 3: Multi-Card Entry & UX Polish

### EPIC-7: Dynamic Multi-Card Entry Form

| Task | Description | Status |
|------|-------------|--------|
| T7.1 | Build quantity picker + dynamic row generator | pending |
| T7.2 | Implement per-row input fields | pending |
| T7.3 | Create POST /api/portfolio/cards/batch | pending |
| T7.4 | Wire multi-card form to batch API | pending |

**UI Concept:**
```
┌─────────────────────────────────────────────────────────────┐
│  ADD TO PORTFOLIO: Sandura of Heliosynth                    │
├─────────────────────────────────────────────────────────────┤
│  How many copies?  [ 4 ]                                    │
│                                                             │
│  ┌─ Copy 1 ──────────────────────────────────────────────┐ │
│  │ Treatment: [Paper ▼]  Source: [eBay ▼]  Price: [$2.50]│ │
│  │ Date: [2024-01-15]    Graded: [ ] PSA/BGS: [   ]      │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌─ Copy 2 ──────────────────────────────────────────────┐ │
│  │ Treatment: [Foil ▼]   Source: [LGS ▼]   Price: [$8.00]│ │
│  │ Date: [2024-01-20]    Graded: [x] PSA: [PSA 10]       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  [x] Same details for all (quick mode)                      │
│                                                             │
│  [Cancel]                              [Add 4 Cards]        │
└─────────────────────────────────────────────────────────────┘
```

---

### EPIC-8: Quick Mode & Smart Defaults

| Task | Description | Status |
|------|-------------|--------|
| T8.1 | "Same details for all" checkbox | pending |
| T8.2 | Smart default: treatment from card's most common | pending |
| T8.3 | Copy row functionality | pending |
| T8.4 | Pre-fill purchase date with today | pending |

---

### EPIC-9: Inline Validation & Error Handling

| Task | Description | Status |
|------|-------------|--------|
| T9.1 | Real-time field validation on blur | pending |
| T9.2 | Form-level error summary | pending |
| T9.3 | Map API errors to form fields | pending |

---

## Phase 4: Bulk Actions & Advanced Features

### EPIC-10: Bulk Edit and Delete

| Task | Description | Status |
|------|-------------|--------|
| T10.1 | Add checkbox column to table | pending |
| T10.2 | Build bulk edit modal | pending |
| T10.3 | Implement bulk delete | pending |
| T10.4 | Create bulk update API endpoints | pending |

---

### EPIC-11: Advanced Filtering and Export

| Task | Description | Status |
|------|-------------|--------|
| T11.1 | Add filter controls (treatment, source, grading) | pending |
| T11.2 | Implement CSV export | pending |
| T11.3 | URL state management for filters | pending |

---

### EPIC-12: Monitoring & Migration Cleanup

| Task | Description | Status |
|------|-------------|--------|
| T12.1 | Add structured logging for portfolio actions | pending |
| T12.2 | Build portfolio analytics dashboard | pending |
| T12.3 | Deprecate old portfolio API (410 Gone) | pending |
| T12.4 | Drop portfolio_item table | pending |

---

## Critical Path

```
EPIC-1 (migration) → EPIC-2 (API) → EPIC-4 (pricing) → EPIC-5 (UI)
                                                            ↓
                                    EPIC-6 (single form) → EPIC-7 (multi form)
                                                            ↓
                                                     EPIC-10 (bulk actions)
```

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Treatment schema unknown | HIGH | Investigate before starting |
| Market pricing by treatment missing | HIGH | May need pricing refactor |
| Large migration (10k+ items) | MEDIUM | Test with prod snapshot, batched migration |
| Batch API timeout (100 cards) | MEDIUM | Load test, async queue if needed |
| Table performance (1000+ rows) | MEDIUM | Virtualization, pagination |

---

## Questions to Resolve Before Starting

1. **Treatment Schema**: Where are treatments stored? Table? Enum? Card metadata?
2. **Market Pricing**: Does pricing already filter by treatment?
3. **Portfolio Size**: How many items exist? Max quantity per item?
4. **Grading Format**: Store as string or structured JSON?

---

## Files to Modify

### Backend
- `/app/models/portfolio.py` - New PortfolioCard model
- `/app/api/portfolio.py` - CRUD endpoints
- `/app/api/schemas/portfolio.py` (new) - Pydantic schemas
- `/scripts/migrate_portfolio.py` (new) - Migration script

### Frontend
- `/frontend/app/routes/portfolio.tsx` - Complete rewrite
- `/frontend/app/components/portfolio/` (new dir)
  - `AddCardModal.tsx`
  - `MultiCardForm.tsx`
  - `TreatmentBadge.tsx`
  - `BulkEditModal.tsx`
