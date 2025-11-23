"""
Integration tests for market API endpoints.

Tests all new price tracking endpoints:
- /api/v1/market/floor
- /api/v1/market/time-series
- /api/v1/market/bid-ask
- /api/v1/market/metrics/{card_id}
"""

import pytest
from fastapi.testclient import TestClient


class TestFloorPriceEndpoint:
    """Test /api/v1/market/floor endpoint."""

    def test_floor_prices_default(self, client: TestClient, multiple_cards):
        """Test floor prices with default parameters."""
        response = client.get("/api/v1/market/floor")

        assert response.status_code == 200
        data = response.json()

        assert "product_type" in data
        assert "period" in data
        assert "by_rarity" in data
        assert "by_treatment" in data
        assert "by_combination" in data

        # Verify structure
        assert isinstance(data["by_rarity"], dict)
        assert isinstance(data["by_treatment"], dict)
        assert isinstance(data["by_combination"], dict)

    def test_floor_prices_by_rarity(self, client: TestClient, multiple_cards):
        """Test floor prices grouped by rarity."""
        response = client.get("/api/v1/market/floor?period=30d")

        assert response.status_code == 200
        data = response.json()

        rarities = data["by_rarity"]
        assert "Common" in rarities
        assert "Rare" in rarities
        assert "Legendary" in rarities

        # Verify data structure
        common = rarities["Common"]
        assert "floor" in common
        assert "count" in common
        assert "avg" in common

        # Verify price ordering
        assert rarities["Common"]["floor"] < rarities["Rare"]["floor"]
        assert rarities["Rare"]["floor"] < rarities["Legendary"]["floor"]

    def test_floor_prices_by_treatment(self, client: TestClient, multiple_cards):
        """Test floor prices grouped by treatment."""
        response = client.get("/api/v1/market/floor?period=30d")

        assert response.status_code == 200
        data = response.json()

        treatments = data["by_treatment"]
        assert "Classic Paper" in treatments
        assert "Classic Foil" in treatments
        assert "OCM Serialized" in treatments

        # Verify price ordering
        assert treatments["Classic Paper"]["floor"] < treatments["Classic Foil"]["floor"]
        assert treatments["Classic Foil"]["floor"] < treatments["OCM Serialized"]["floor"]

    def test_floor_prices_time_periods(self, client: TestClient, multiple_cards):
        """Test floor prices with different time periods."""
        periods = ["1d", "7d", "14d", "30d", "90d"]

        for period in periods:
            response = client.get(f"/api/v1/market/floor?period={period}")
            assert response.status_code == 200

            data = response.json()
            assert data["period"] == period

    def test_floor_prices_min_sales_filter(self, client: TestClient, multiple_cards):
        """Test floor prices with min_sales parameter."""
        # Get with low min_sales
        response_low = client.get("/api/v1/market/floor?min_sales=1")
        assert response_low.status_code == 200

        # Get with high min_sales
        response_high = client.get("/api/v1/market/floor?min_sales=10")
        assert response_high.status_code == 200

        data_low = response_low.json()
        data_high = response_high.json()

        # Higher min_sales should have fewer or equal combinations
        assert len(data_high["by_combination"]) <= len(data_low["by_combination"])

    def test_floor_prices_box_products(self, client: TestClient, box_product):
        """Test floor prices for box products."""
        response = client.get("/api/v1/market/floor?product_type=Box")

        assert response.status_code == 200
        data = response.json()

        assert data["product_type"] == "Box"

    def test_floor_prices_invalid_period(self, client: TestClient, multiple_cards):
        """Test floor prices with invalid period."""
        response = client.get("/api/v1/market/floor?period=invalid")

        assert response.status_code == 422  # Validation error


class TestTimeSeriesEndpoint:
    """Test /api/v1/market/time-series endpoint."""

    def test_time_series_single_card(self, client: TestClient, test_card, test_prices):
        """Test time series for a single card."""
        response = client.get(
            f"/api/v1/market/time-series?card_id={test_card.id}&interval=1d&period=30d"
        )

        assert response.status_code == 200
        data = response.json()

        assert "card_id" in data
        assert "interval" in data
        assert "period" in data
        assert "data" in data

        assert data["card_id"] == test_card.id
        assert data["interval"] == "1d"
        assert data["period"] == "30d"

        # Verify data points
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Check data structure
        for point in data["data"]:
            assert "date" in point
            assert "vwap" in point
            assert "floor" in point
            assert "ceiling" in point
            assert "volume" in point

    def test_time_series_product_type(self, client: TestClient, multiple_cards):
        """Test time series for product type aggregate."""
        response = client.get(
            "/api/v1/market/time-series?product_type=Single&interval=1d&period=7d"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["product_type"] == "Single"
        assert "data" in data
        assert len(data["data"]) > 0

    def test_time_series_weekly_interval(self, client: TestClient, test_card, test_prices):
        """Test time series with weekly interval."""
        response = client.get(
            f"/api/v1/market/time-series?card_id={test_card.id}&interval=1w&period=30d"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["interval"] == "1w"
        # Should have ~4 weekly data points
        assert 3 <= len(data["data"]) <= 5

    def test_time_series_monthly_interval(self, client: TestClient, test_card, test_prices):
        """Test time series with monthly interval."""
        response = client.get(
            f"/api/v1/market/time-series?card_id={test_card.id}&interval=1m&period=90d"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["interval"] == "1m"

    def test_time_series_missing_parameters(self, client: TestClient):
        """Test time series without card_id or product_type."""
        response = client.get("/api/v1/market/time-series?interval=1d&period=7d")

        assert response.status_code == 400  # Bad request
        assert "card_id or product_type must be specified" in response.json()["detail"]

    def test_time_series_invalid_interval(self, client: TestClient, test_card):
        """Test time series with invalid interval."""
        response = client.get(
            f"/api/v1/market/time-series?card_id={test_card.id}&interval=invalid&period=7d"
        )

        assert response.status_code == 422  # Validation error

    def test_time_series_no_data(self, client: TestClient, test_card):
        """Test time series when no price data exists."""
        response = client.get(
            f"/api/v1/market/time-series?card_id={test_card.id}&interval=1d&period=7d"
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty array
        assert data["data"] == []


class TestBidAskEndpoint:
    """Test /api/v1/market/bid-ask endpoint."""

    def test_bid_ask_spreads(self, client: TestClient, test_card, test_snapshot):
        """Test bid/ask spreads endpoint."""
        response = client.get("/api/v1/market/bid-ask?product_type=Single&limit=50")

        assert response.status_code == 200
        data = response.json()

        assert "product_type" in data
        assert "count" in data
        assert "cards" in data

        assert data["product_type"] == "Single"
        assert isinstance(data["cards"], list)

        # Check card structure
        if len(data["cards"]) > 0:
            card = data["cards"][0]
            assert "card_id" in card
            assert "name" in card
            assert "lowest_ask" in card
            assert "highest_bid" in card
            assert "spread_amount" in card
            assert "spread_percent" in card
            assert "price_to_sale" in card

    def test_bid_ask_sorted_by_spread(self, client: TestClient, multiple_cards, session):
        """Test that results are sorted by spread percentage."""
        # Create snapshots with different spreads
        from app.models.market import MarketSnapshot
        from datetime import datetime

        for i, card in enumerate(multiple_cards):
            snapshot = MarketSnapshot(
                card_id=card.id,
                min_price=10.0,
                max_price=50.0,
                avg_price=25.0,
                volume=100,
                lowest_ask=25.0 + (i * 10.0),  # Increasing ask prices
                highest_bid=20.0,
                inventory=10,
                platform="ebay",
                timestamp=datetime.utcnow()
            )
            session.add(snapshot)
        session.commit()

        response = client.get("/api/v1/market/bid-ask?limit=10")

        assert response.status_code == 200
        data = response.json()

        cards = data["cards"]
        if len(cards) > 1:
            # Verify sorted descending by spread_percent
            for i in range(len(cards) - 1):
                assert cards[i]["spread_percent"] >= cards[i + 1]["spread_percent"]

    def test_bid_ask_limit_parameter(self, client: TestClient, multiple_cards):
        """Test bid/ask with limit parameter."""
        response = client.get("/api/v1/market/bid-ask?limit=2")

        assert response.status_code == 200
        data = response.json()

        # Should respect limit
        assert len(data["cards"]) <= 2

    def test_bid_ask_box_products(self, client: TestClient, box_product):
        """Test bid/ask for box products."""
        response = client.get("/api/v1/market/bid-ask?product_type=Box")

        assert response.status_code == 200
        data = response.json()

        assert data["product_type"] == "Box"


class TestComprehensiveMetricsEndpoint:
    """Test /api/v1/market/metrics/{card_id} endpoint."""

    def test_comprehensive_metrics(self, client: TestClient, test_card, test_prices, test_snapshot):
        """Test comprehensive metrics endpoint."""
        response = client.get(f"/api/v1/market/metrics/{test_card.id}?period=30d")

        assert response.status_code == 200
        data = response.json()

        # Basic card info
        assert "card_id" in data
        assert "name" in data
        assert "set_name" in data
        assert "product_type" in data
        assert "period" in data

        # Snapshot data
        assert "min_price" in data
        assert "max_price" in data
        assert "avg_price" in data
        assert "volume" in data
        assert "lowest_ask" in data
        assert "inventory" in data

        # Calculated metrics
        assert "vwap" in data
        assert "ema_7d" in data
        assert "ema_14d" in data
        assert "ema_30d" in data
        assert "price_delta_1d" in data
        assert "price_delta_7d" in data
        assert "price_delta_30d" in data
        assert "bid_ask_spread" in data
        assert "price_to_sale" in data

        # Verify values
        assert data["card_id"] == test_card.id
        assert data["period"] == "30d"

        # VWAP should be calculated
        assert data["vwap"] is not None
        assert data["vwap"] > 0

    def test_metrics_different_periods(self, client: TestClient, test_card, test_prices, test_snapshot):
        """Test metrics with different time periods."""
        periods = ["1d", "7d", "14d", "30d"]

        for period in periods:
            response = client.get(f"/api/v1/market/metrics/{test_card.id}?period={period}")

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == period

    def test_metrics_card_not_found(self, client: TestClient):
        """Test metrics for non-existent card."""
        response = client.get("/api/v1/market/metrics/99999?period=30d")

        assert response.status_code == 404
        assert "Card not found" in response.json()["detail"]

    def test_metrics_invalid_period(self, client: TestClient, test_card):
        """Test metrics with invalid period."""
        response = client.get(f"/api/v1/market/metrics/{test_card.id}?period=invalid")

        assert response.status_code == 422  # Validation error

    def test_metrics_partial_data(self, client: TestClient, test_card, session):
        """Test metrics when some data is missing."""
        # Clear snapshots
        from app.models.market import MarketSnapshot
        session.query(MarketSnapshot).filter(
            MarketSnapshot.card_id == test_card.id
        ).delete()
        session.commit()

        response = client.get(f"/api/v1/market/metrics/{test_card.id}?period=7d")

        assert response.status_code == 200
        data = response.json()

        # Snapshot fields should be None
        assert data["min_price"] is None
        assert data["max_price"] is None
        assert data["avg_price"] is None

        # But calculated metrics might still work if price data exists


class TestExistingEndpoints:
    """Test that existing endpoints still work correctly."""

    def test_treatments_endpoint(self, client: TestClient, multiple_cards):
        """Test /api/v1/market/treatments endpoint."""
        response = client.get("/api/v1/market/treatments")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check structure
        for treatment in data:
            assert "name" in treatment
            assert "min_price" in treatment
            assert "count" in treatment

    def test_market_overview_endpoint(self, client: TestClient, test_card, test_prices):
        """Test /api/v1/market/overview endpoint."""
        response = client.get("/api/v1/market/overview?time_period=24h")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            card = data[0]
            assert "id" in card
            assert "name" in card
            assert "vwap" in card  # Should now include VWAP

    def test_market_activity_endpoint(self, client: TestClient, test_card, test_prices):
        """Test /api/v1/market/activity endpoint."""
        response = client.get("/api/v1/market/activity?limit=20")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        if len(data) > 0:
            sale = data[0]
            assert "card_id" in sale
            assert "card_name" in sale
            assert "price" in sale
            assert "treatment" in sale


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_product_type(self, client: TestClient):
        """Test endpoints with invalid product type."""
        response = client.get("/api/v1/market/floor?product_type=Invalid")

        # Should still work, just return no results
        assert response.status_code == 200

    def test_negative_limit(self, client: TestClient):
        """Test bid/ask with negative limit."""
        response = client.get("/api/v1/market/bid-ask?limit=-1")

        # Should use validation
        assert response.status_code == 422

    def test_zero_min_sales(self, client: TestClient):
        """Test floor prices with zero min_sales."""
        response = client.get("/api/v1/market/floor?min_sales=0")

        # Should fail validation (min=1)
        assert response.status_code == 422

    def test_excessive_limit(self, client: TestClient, multiple_cards):
        """Test bid/ask with limit exceeding max."""
        response = client.get("/api/v1/market/bid-ask?limit=1000")

        # Should enforce max limit (200)
        assert response.status_code == 422
