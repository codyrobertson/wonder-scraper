# Wonder Scraper Test Suite

Comprehensive test suite for the price tracking system.

## Test Structure

```
tests/
├── __init__.py                     # Package initialization
├── conftest.py                     # Pytest fixtures and test database setup
├── test_price_calculator.py        # Unit tests for PriceCalculator service
├── test_market_api.py             # Integration tests for market API endpoints
├── test_cards_api.py              # Integration tests for cards API endpoints
└── README.md                       # This file
```

## Test Coverage

### PriceCalculator Service Tests (`test_price_calculator.py`)

**VWAP Calculation** (4 tests)
- 30-day period calculation
- 7-day period calculation
- No data handling
- All-time period calculation

**EMA Calculation** (3 tests)
- 14-day window calculation
- Different window comparisons (7d, 14d, 30d)
- Insufficient data handling

**Price Delta** (4 tests)
- 1-day delta calculation
- 30-day delta comparison
- No data handling
- All-time delta calculation

**Floor Prices** (4 tests)
- Floor by rarity
- Floor by treatment
- Floor by rarity+treatment combination
- Min sales filter validation

**Bid/Ask Spread** (3 tests)
- Basic spread calculation
- No snapshot handling
- No bid handling

**Price-to-Sale Ratio** (3 tests)
- Basic ratio calculation
- No VWAP handling
- No ask price handling

**Time Series** (4 tests)
- Single card time series
- Product type aggregate
- Weekly interval
- No data handling

**Comprehensive Metrics** (2 tests)
- All metrics aggregation
- Partial data handling

**Edge Cases** (3 tests)
- Invalid time periods
- Zero prices
- Single data point

**Total: 30 unit tests**

### Market API Tests (`test_market_api.py`)

**Floor Price Endpoint** (6 tests)
- Default parameters
- By rarity grouping
- By treatment grouping
- Time period variations
- Min sales filter
- Box products

**Time Series Endpoint** (7 tests)
- Single card series
- Product type aggregate
- Weekly interval
- Monthly interval
- Missing parameters
- Invalid interval
- No data handling

**Bid/Ask Endpoint** (4 tests)
- Basic spreads
- Sorted by spread
- Limit parameter
- Box products

**Comprehensive Metrics Endpoint** (4 tests)
- All metrics
- Different periods
- Card not found
- Invalid period

**Existing Endpoints** (3 tests)
- Treatments endpoint
- Market overview
- Market activity

**Error Handling** (4 tests)
- Invalid product type
- Negative limit
- Zero min sales
- Excessive limit

**Total: 28 integration tests**

### Cards API Tests (`test_cards_api.py`)

**Cards Endpoint** (9 tests)
- Default parameters
- New time periods (1d, 3d, 14d)
- Existing time periods
- Product type filter
- Search parameter
- Pagination
- Invalid time period
- Response structure
- VWAP vs latest_price

**Cards Market Endpoint** (4 tests)
- VWAP included
- VWAP calculation
- No VWAP data
- Not found

**Card Detail Endpoint** (2 tests)
- Basic detail
- Not found

**Caching** (2 tests)
- Cache hit
- Different parameters

**Backward Compatibility** (4 tests)
- 24h period
- All period
- Product type filter
- Search parameter

**Total: 21 integration tests**

## Running Tests

### Run All Tests

```bash
# Using poetry
poetry run pytest

# Or directly with pytest
pytest
```

### Run Specific Test File

```bash
poetry run pytest tests/test_price_calculator.py
poetry run pytest tests/test_market_api.py
poetry run pytest tests/test_cards_api.py
```

### Run Specific Test Class

```bash
poetry run pytest tests/test_price_calculator.py::TestVWAPCalculation
poetry run pytest tests/test_market_api.py::TestFloorPriceEndpoint
```

### Run Specific Test

```bash
poetry run pytest tests/test_price_calculator.py::TestVWAPCalculation::test_vwap_30d_period
```

### Run with Verbose Output

```bash
poetry run pytest -v
```

### Run with Coverage Report

```bash
poetry run pytest --cov=app.services.price_calculator --cov=app.api.market
poetry run pytest --cov=app --cov-report=html
```

### Run with Markers

```bash
# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration
```

## Test Fixtures

### Database Fixtures

- **engine**: In-memory SQLite database
- **session**: Database session
- **client**: FastAPI test client

### Data Fixtures

- **test_rarity**: Single rarity (Legendary)
- **test_card**: Single test card
- **test_prices**: 30 days of price data (90 sales)
- **test_snapshot**: Market snapshot
- **multiple_cards**: 3 cards with different rarities and treatments
- **active_listings**: Active buy-it-now listings
- **box_product**: Box product with sales

## Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test session
- Isolated from production/development databases
- Fast (no disk I/O)
- Automatically cleaned up

## Writing New Tests

### Example Unit Test

```python
def test_new_calculation(session: Session, test_card: Card, test_prices):
    """Test description."""
    calc = PriceCalculator(session)
    result = calc.new_method(test_card.id)

    assert result is not None
    assert result > 0
```

### Example Integration Test

```python
def test_new_endpoint(client: TestClient, test_card):
    """Test description."""
    response = client.get(f"/api/v1/endpoint/{test_card.id}")

    assert response.status_code == 200
    data = response.json()

    assert "field" in data
    assert data["field"] > 0
```

## Best Practices

1. **Descriptive Test Names**: Use clear, descriptive names that explain what is being tested
2. **Single Assertion Focus**: Each test should verify one behavior
3. **Use Fixtures**: Leverage pytest fixtures for test data
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Isolation**: Tests should be independent and not rely on execution order
6. **Clean Setup/Teardown**: Use fixtures for setup and let pytest handle cleanup

## Continuous Integration

Tests should be run:
- Before every commit
- In CI/CD pipeline
- Before deploying to production
- After dependency updates

## Coverage Goals

- **Service Layer**: 90%+ coverage
- **API Endpoints**: 80%+ coverage
- **Edge Cases**: All major error paths covered

## Troubleshooting

### Tests Failing Locally

1. Check that test database is clean:
   ```bash
   poetry run pytest --cache-clear
   ```

2. Verify dependencies are installed:
   ```bash
   poetry install
   ```

3. Check for conflicting fixtures or data

### Slow Tests

- Check database queries for N+1 problems
- Use smaller datasets in fixtures
- Consider using pytest-xdist for parallel execution:
  ```bash
  poetry run pytest -n auto
  ```

### Import Errors

- Ensure `app` package is importable
- Check Python path configuration
- Verify test discovery is working

## Next Steps

1. Add performance tests for high-load scenarios
2. Add integration tests with real database
3. Add end-to-end tests with frontend
4. Set up coverage reporting in CI/CD
5. Add mutation testing for test quality

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
