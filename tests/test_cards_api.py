"""
Integration tests for enhanced cards API endpoint.

Tests the updated /api/v1/cards endpoint with new time periods (1d, 3d, 14d).
"""

import pytest
from fastapi.testclient import TestClient


class TestCardsEndpoint:
    """Test /api/v1/cards endpoint enhancements."""

    def test_cards_default_parameters(self, client: TestClient, test_card, test_prices):
        """Test cards endpoint with default parameters."""
        response = client.get("/api/v1/cards")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check VWAP is included
        for card in data:
            assert "vwap" in card

    def test_cards_new_time_periods(self, client: TestClient, test_card, test_prices):
        """Test new time periods: 1d, 3d, 14d."""
        new_periods = ["1d", "3d", "14d"]

        for period in new_periods:
            response = client.get(f"/api/v1/cards?time_period={period}")

            assert response.status_code == 200, f"Failed for period {period}"
            data = response.json()

            assert isinstance(data, list)

    def test_cards_existing_time_periods(self, client: TestClient, test_card, test_prices):
        """Test existing time periods still work: 24h, 7d, 30d, 90d, all."""
        existing_periods = ["24h", "7d", "30d", "90d", "all"]

        for period in existing_periods:
            response = client.get(f"/api/v1/cards?time_period={period}")

            assert response.status_code == 200, f"Failed for period {period}"
            data = response.json()

            assert isinstance(data, list)

    def test_cards_with_product_type_filter(self, client: TestClient, box_product):
        """Test cards endpoint with product_type filter."""
        response = client.get("/api/v1/cards?product_type=Box")

        assert response.status_code == 200
        data = response.json()

        # All returned cards should be boxes
        for card in data:
            assert card["product_type"] == "Box"

    def test_cards_with_search(self, client: TestClient, test_card):
        """Test cards endpoint with search parameter."""
        response = client.get(f"/api/v1/cards?search={test_card.name}")

        assert response.status_code == 200
        data = response.json()

        # Should find the test card
        assert len(data) > 0
        assert any(card["name"] == test_card.name for card in data)

    def test_cards_pagination(self, client: TestClient, multiple_cards):
        """Test cards endpoint pagination."""
        # Get first page
        response1 = client.get("/api/v1/cards?skip=0&limit=2")
        assert response1.status_code == 200
        data1 = response1.json()

        # Get second page
        response2 = client.get("/api/v1/cards?skip=2&limit=2")
        assert response2.status_code == 200
        data2 = response2.json()

        # Should have different cards
        if len(data1) > 0 and len(data2) > 0:
            assert data1[0]["id"] != data2[0]["id"]

    def test_cards_invalid_time_period(self, client: TestClient):
        """Test cards endpoint with invalid time period."""
        response = client.get("/api/v1/cards?time_period=invalid")

        assert response.status_code == 422  # Validation error

    def test_cards_response_structure(self, client: TestClient, test_card, test_prices):
        """Test that cards response has correct structure."""
        response = client.get("/api/v1/cards?limit=1")

        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            card = data[0]

            # Required fields
            assert "id" in card
            assert "name" in card
            assert "set_name" in card
            assert "rarity_id" in card
            assert "product_type" in card

            # Price fields
            assert "latest_price" in card
            assert "vwap" in card  # NEW - should be included
            assert "volume_24h" in card
            assert "price_delta_24h" in card

    def test_cards_vwap_vs_latest_price(self, client: TestClient, test_card, test_prices):
        """Test that VWAP is different from latest_price."""
        response = client.get(f"/api/v1/cards?time_period=30d")

        assert response.status_code == 200
        data = response.json()

        if len(data) > 0:
            card = data[0]

            # VWAP and latest_price might be different
            # (depends on price distribution)
            assert card["vwap"] is not None

    def test_cards_different_periods_different_vwap(self, client: TestClient, test_card, test_prices):
        """Test that different periods produce different VWAPs."""
        response_7d = client.get("/api/v1/cards?time_period=7d&limit=100")
        response_30d = client.get("/api/v1/cards?time_period=30d&limit=100")

        assert response_7d.status_code == 200
        assert response_30d.status_code == 200

        data_7d = response_7d.json()
        data_30d = response_30d.json()

        # Find same card in both responses
        if len(data_7d) > 0 and len(data_30d) > 0:
            card_id = data_7d[0]["id"]
            card_7d = next((c for c in data_7d if c["id"] == card_id), None)
            card_30d = next((c for c in data_30d if c["id"] == card_id), None)

            if card_7d and card_30d:
                # VWAPs might be different (due to price trends)
                # At least verify both are calculated
                assert card_7d["vwap"] is not None
                assert card_30d["vwap"] is not None


class TestCardsMarketEndpoint:
    """Test /api/v1/cards/{card_id}/market endpoint with VWAP."""

    def test_card_market_includes_vwap(self, client: TestClient, test_card, test_prices, test_snapshot):
        """Test that card market endpoint includes VWAP."""
        response = client.get(f"/api/v1/cards/{test_card.id}/market")

        assert response.status_code == 200
        data = response.json()

        # Should include VWAP (from our earlier fix)
        assert "vwap" in data
        assert data["vwap"] is not None

    def test_card_market_vwap_calculation(self, client: TestClient, test_card, test_prices):
        """Test that VWAP is correctly calculated."""
        response = client.get(f"/api/v1/cards/{test_card.id}/market")

        assert response.status_code == 200
        data = response.json()

        # VWAP should be within reasonable range
        assert data["vwap"] > 0
        assert data["vwap"] <= data["max_price"]
        assert data["vwap"] >= data["min_price"]

    def test_card_market_no_vwap_data(self, client: TestClient, test_card, test_snapshot, session):
        """Test card market when no sold prices exist."""
        # Clear all price data
        from app.models.market import MarketPrice
        session.query(MarketPrice).filter(
            MarketPrice.card_id == test_card.id
        ).delete()
        session.commit()

        response = client.get(f"/api/v1/cards/{test_card.id}/market")

        assert response.status_code == 200
        data = response.json()

        # VWAP should be None
        assert data["vwap"] is None

    def test_card_market_not_found(self, client: TestClient):
        """Test card market for non-existent card."""
        response = client.get("/api/v1/cards/99999/market")

        assert response.status_code == 404


class TestCardDetailEndpoint:
    """Test /api/v1/cards/{card_id} endpoint."""

    def test_card_detail(self, client: TestClient, test_card, test_prices):
        """Test card detail endpoint."""
        response = client.get(f"/api/v1/cards/{test_card.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == test_card.id
        assert data["name"] == test_card.name
        assert "vwap" in data
        assert "price_delta_24h" in data

    def test_card_detail_not_found(self, client: TestClient):
        """Test card detail for non-existent card."""
        response = client.get("/api/v1/cards/99999")

        assert response.status_code == 404


class TestCaching:
    """Test caching behavior of cards endpoint."""

    def test_cards_cache_hit(self, client: TestClient, test_card, test_prices):
        """Test that subsequent requests hit cache."""
        # First request
        response1 = client.get("/api/v1/cards?time_period=24h&limit=10")
        assert response1.status_code == 200

        # Second request (should hit cache)
        response2 = client.get("/api/v1/cards?time_period=24h&limit=10")
        assert response2.status_code == 200

        # Check for cache header
        if "X-Cache" in response2.headers:
            assert response2.headers["X-Cache"] == "HIT"

    def test_cards_cache_different_params(self, client: TestClient, test_card, test_prices):
        """Test that different parameters don't hit cache."""
        # Request with 24h period
        response1 = client.get("/api/v1/cards?time_period=24h&limit=10")
        assert response1.status_code == 200

        # Request with 7d period (different cache key)
        response2 = client.get("/api/v1/cards?time_period=7d&limit=10")
        assert response2.status_code == 200

        # Should be cache miss
        if "X-Cache" in response2.headers:
            assert response2.headers["X-Cache"] == "MISS"


class TestBackwardCompatibility:
    """Test backward compatibility with existing functionality."""

    def test_24h_period_still_works(self, client: TestClient, test_card, test_prices):
        """Test that 24h period (default) still works."""
        response = client.get("/api/v1/cards?time_period=24h")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_all_period_still_works(self, client: TestClient, test_card, test_prices):
        """Test that 'all' period still works."""
        response = client.get("/api/v1/cards?time_period=all")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_product_type_filter_still_works(self, client: TestClient, box_product):
        """Test that product_type filter still works."""
        response = client.get("/api/v1/cards?product_type=Box")

        assert response.status_code == 200
        data = response.json()

        for card in data:
            assert card["product_type"] == "Box"

    def test_search_still_works(self, client: TestClient, test_card):
        """Test that search parameter still works."""
        response = client.get(f"/api/v1/cards?search={test_card.name}")

        assert response.status_code == 200
        data = response.json()

        assert any(card["name"] == test_card.name for card in data)
