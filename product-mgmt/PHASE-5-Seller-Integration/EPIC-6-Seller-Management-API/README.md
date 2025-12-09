# EPIC-6: Seller Management API

**Status**: Planned
**Sprint**: 3
**Priority**: High
**Dependencies**: EPIC-5 (Database Schema)

---

## Objective

RESTful API endpoints for managing sellers, inventory, and SKU mappings.

## User Impact

Admins can manage seller data programmatically.

## Tech Scope

- FastAPI endpoints
- Pydantic schemas
- Authentication/authorization
- OpenAPI documentation

---

## Done-When Criteria

- [ ] All CRUD operations return proper HTTP status codes (200/201/400/404)
- [ ] Pagination implemented for list endpoints
- [ ] API key authentication enforced for write operations
- [ ] Swagger docs generated and accurate
- [ ] Integration tests with 80%+ coverage

---

## API Endpoints

### Seller CRUD
```
GET    /api/sellers           # List with pagination, filters
GET    /api/sellers/{id}      # Get seller detail
POST   /api/sellers           # Create seller
PUT    /api/sellers/{id}      # Update seller
DELETE /api/sellers/{id}      # Soft delete seller
POST   /api/sellers/{id}/merge  # Merge duplicate sellers
```

### Inventory
```
GET    /api/sellers/{id}/inventory  # Current inventory for seller
POST   /api/sellers/{id}/inventory  # Add/update inventory items
GET    /api/inventory/search        # Search across all sellers
GET    /api/inventory/snapshots     # Historical snapshots
```

### SKU Mappings
```
GET    /api/sku-mappings              # List with filters
POST   /api/sku-mappings              # Create mapping
PUT    /api/sku-mappings/{id}         # Update mapping
DELETE /api/sku-mappings/{id}         # Delete mapping
GET    /api/sku-mappings/resolve      # Lookup card by SKU
PUT    /api/sku-mappings/bulk-verify  # Bulk approve mappings
```

---

## Tasks

### T2.1 — Seller CRUD Endpoints

**UOWs**:
- U2.1.1: Create Pydantic schemas for Seller (2h)
- U2.1.2: Create /api/sellers router (4h)
- U2.1.3: Add sellers router to main app (30m)
- U2.1.4: Add authentication to write operations (1h)

### T2.2 — Inventory Endpoints

**UOWs**:
- U2.2.1: Create SellerInventory schemas (2h)
- U2.2.2: Implement GET /sellers/{id}/inventory (2h)
- U2.2.3: Implement POST /sellers/{id}/inventory (3h)
- U2.2.4: Implement GET /api/inventory/search (2h)

### T2.3 — SKU Mapping Endpoints

**UOWs**:
- U2.3.1: Create SKUMapping schemas (1.5h)
- U2.3.2: Create /api/sku-mappings router (3h)
- U2.3.3: Implement GET /sku-mappings/resolve (2h)
- U2.3.4: Add sku-mappings router to main app (30m)

### T2.4 — Inventory Snapshot Endpoints

**UOWs**:
- U2.4.1: Create InventorySnapshot schemas (1.5h)
- U2.4.2: Implement GET /inventory/snapshots (2h)

### T2.5 — API Integration Tests

**UOWs**:
- U2.5.1: Create test_sellers_api.py (3h)
- U2.5.2: Create test_inventory_api.py (3h)
- U2.5.3: Create test_sku_mappings_api.py (2h)

---

## Pydantic Schemas

### SellerBase
```python
class SellerBase(BaseModel):
    platform: str
    platform_seller_id: str
    display_name: Optional[str] = None
    feedback_score: Optional[int] = None
    feedback_percent: Optional[float] = None
```

### SellerCreate / SellerUpdate
```python
class SellerCreate(SellerBase):
    metadata: Optional[dict] = None

class SellerUpdate(BaseModel):
    display_name: Optional[str] = None
    feedback_score: Optional[int] = None
    feedback_percent: Optional[float] = None
    metadata: Optional[dict] = None
```

### SellerRead
```python
class SellerRead(SellerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    inventory_count: Optional[int] = None
    sales_count_30d: Optional[int] = None
```

---

## Required Documentation

- `/docs/API_REFERENCE.md` - Endpoint specifications with examples
- `/docs/AUTHENTICATION.md` - API key usage and permissions
