"""
Unit tests for PriceCalculator service.

Tests all price calculation methods including VWAP, EMA, floor prices,
price deltas, bid/ask spreads, and time series data.
"""

import pytest
from datetime import datetime, timedelta
from sqlmodel import Session

from app.services.price_calculator import PriceCalculator
from app.models.card import Card
from app.models.market import MarketPrice, MarketSnapshot


class TestVWAPCalculation:
    """Test VWAP calculation methods."""

    def test_vwap_30d_period(self, session: Session, test_card: Card, test_prices):
        """Test VWAP calculation over 30-day period."""
        calc = PriceCalculator(session)
        vwap = calc.calculate_vwap(test_card.id, period="30d")

        assert vwap is not None
        assert isinstance(vwap, float)
        # VWAP should be around $20 (midpoint of $10-$30 range)
        assert 15.0 < vwap < 25.0

    def test_vwap_7d_period(self, session: Session, test_card: Card, test_prices):
        """Test VWAP calculation over 7-day period."""
        calc = PriceCalculator(session)
        vwap = calc.calculate_vwap(test_card.id, period="7d")

        assert vwap is not None
        # Recent 7 days should have higher prices (trending up)
        vwap_30d = calc.calculate_vwap(test_card.id, period="30d")
        assert vwap > vwap_30d

    def test_vwap_no_data(self, session: Session, test_card: Card):
        """Test VWAP when no price data exists."""
        # Clear all prices
        session.query(MarketPrice).filter(
            MarketPrice.card_id == test_card.id
        ).delete()
        session.commit()

        calc = PriceCalculator(session)
        vwap = calc.calculate_vwap(test_card.id, period="30d")

        assert vwap is None

    def test_vwap_all_time(self, session: Session, test_card: Card, test_prices):
        """Test VWAP for all time period."""
        calc = PriceCalculator(session)
        vwap = calc.calculate_vwap(test_card.id, period="all")

        assert vwap is not None
        assert vwap > 0


class TestEMACalculation:
    """Test Exponential Moving Average calculations."""

    def test_ema_14d_window(self, session: Session, test_card: Card, test_prices):
        """Test EMA with 14-day window."""
        calc = PriceCalculator(session)
        ema = calc.calculate_ema(test_card.id, period="30d", window=14)

        assert ema is not None
        assert isinstance(ema, float)
        assert ema > 0

    def test_ema_different_windows(self, session: Session, test_card: Card, test_prices):
        """Test that different EMA windows produce different results."""
        calc = PriceCalculator(session)

        ema_7 = calc.calculate_ema(test_card.id, period="30d", window=7)
        ema_14 = calc.calculate_ema(test_card.id, period="30d", window=14)
        ema_30 = calc.calculate_ema(test_card.id, period="30d", window=30)

        assert ema_7 is not None
        assert ema_14 is not None
        assert ema_30 is not None

        # Shorter windows should be more reactive to recent price changes
        # Since prices are trending up, shorter EMA should be higher
        assert ema_7 > ema_14
        assert ema_14 > ema_30

    def test_ema_insufficient_data(self, session: Session, test_card: Card):
        """Test EMA when insufficient data points exist."""
        # Delete most prices
        session.query(MarketPrice).filter(
            MarketPrice.card_id == test_card.id
        ).delete()
        session.commit()

        # Add only 5 prices (less than window of 14)
        now = datetime.utcnow()
        for i in range(5):
            price = MarketPrice(
                card_id=test_card.id,
                price=10.0 + i,
                title=f"Test {i}",
                sold_date=now - timedelta(days=4 - i),
                listing_type="sold",
                treatment="Classic Paper",
                platform="ebay",
                scraped_at=now
            )
            session.add(price)
        session.commit()

        calc = PriceCalculator(session)
        ema = calc.calculate_ema(test_card.id, period="30d", window=14)

        assert ema is None  # Not enough data for 14-day window


class TestPriceDelta:
    """Test price delta (percentage change) calculations."""

    def test_price_delta_1d(self, session: Session, test_card: Card, test_prices):
        """Test 1-day price delta calculation."""
        calc = PriceCalculator(session)
        delta = calc.calculate_price_delta(test_card.id, period="1d")

        assert delta is not None
        assert isinstance(delta, float)
        # Prices are trending up, so delta should be positive
        assert delta > 0

    def test_price_delta_30d(self, session: Session, test_card: Card, test_prices):
        """Test 30-day price delta shows larger change."""
        calc = PriceCalculator(session)

        delta_1d = calc.calculate_price_delta(test_card.id, period="1d")
        delta_30d = calc.calculate_price_delta(test_card.id, period="30d")

        assert delta_1d is not None
        assert delta_30d is not None

        # 30-day delta should be larger (more time for price to change)
        assert abs(delta_30d) > abs(delta_1d)

    def test_price_delta_no_data(self, session: Session, test_card: Card):
        """Test price delta when no data exists."""
        session.query(MarketPrice).filter(
            MarketPrice.card_id == test_card.id
        ).delete()
        session.commit()

        calc = PriceCalculator(session)
        delta = calc.calculate_price_delta(test_card.id, period="7d")

        assert delta is None

    def test_price_delta_all_time(self, session: Session, test_card: Card, test_prices):
        """Test price delta for all time period."""
        calc = PriceCalculator(session)
        delta = calc.calculate_price_delta(test_card.id, period="all")

        assert delta is not None
        # Should show large increase from $10 to $30
        assert delta > 50  # More than 50% increase


class TestFloorPrices:
    """Test floor price calculations."""

    def test_floor_by_rarity(self, session: Session, multiple_cards):
        """Test floor price calculation by rarity."""
        calc = PriceCalculator(session)
        floors = calc.calculate_floor_by_rarity(
            rarity_id=None,
            period="30d",
            product_type="Single"
        )

        assert "Common" in floors
        assert "Rare" in floors
        assert "Legendary" in floors

        # Verify floor structure
        assert "floor" in floors["Common"]
        assert "count" in floors["Common"]
        assert "avg" in floors["Common"]

        # Verify floor ordering (Common < Rare < Legendary)
        assert floors["Common"]["floor"] < floors["Rare"]["floor"]
        assert floors["Rare"]["floor"] < floors["Legendary"]["floor"]

    def test_floor_by_treatment(self, session: Session, multiple_cards):
        """Test floor price calculation by treatment."""
        calc = PriceCalculator(session)
        floors = calc.calculate_floor_by_treatment(
            treatment=None,
            period="30d",
            product_type="Single"
        )

        assert "Classic Paper" in floors
        assert "Classic Foil" in floors
        assert "OCM Serialized" in floors

        # Verify pricing order
        assert floors["Classic Paper"]["floor"] < floors["Classic Foil"]["floor"]
        assert floors["Classic Foil"]["floor"] < floors["OCM Serialized"]["floor"]

    def test_floor_by_combination(self, session: Session, multiple_cards):
        """Test floor price by rarity + treatment combination."""
        calc = PriceCalculator(session)
        floors = calc.calculate_floor_by_combination(
            period="30d",
            product_type="Single",
            min_sales=3
        )

        # Should have combinations like "Legendary_OCM Serialized"
        assert len(floors) > 0

        for combo, data in floors.items():
            assert "_" in combo  # Should have rarity_treatment format
            assert data["count"] >= 3  # Respects min_sales
            assert data["floor"] > 0
            assert data["avg"] >= data["floor"]

    def test_floor_min_sales_filter(self, session: Session, multiple_cards):
        """Test that min_sales filter works correctly."""
        calc = PriceCalculator(session)

        floors_low = calc.calculate_floor_by_combination(
            period="30d",
            product_type="Single",
            min_sales=1
        )

        floors_high = calc.calculate_floor_by_combination(
            period="30d",
            product_type="Single",
            min_sales=10
        )

        # Higher min_sales should have fewer combinations
        assert len(floors_high) <= len(floors_low)


class TestBidAskSpread:
    """Test bid/ask spread calculations."""

    def test_bid_ask_spread(self, session: Session, test_card: Card, test_snapshot):
        """Test bid/ask spread calculation."""
        calc = PriceCalculator(session)
        spread = calc.calculate_bid_ask_spread(test_card.id)

        assert spread is not None
        assert "lowest_ask" in spread
        assert "highest_bid" in spread
        assert "spread_amount" in spread
        assert "spread_percent" in spread

        # From fixture: ask=28, bid=24
        assert spread["lowest_ask"] == 28.0
        assert spread["highest_bid"] == 24.0
        assert spread["spread_amount"] == 4.0
        assert spread["spread_percent"] == pytest.approx(14.29, rel=0.1)

    def test_bid_ask_no_snapshot(self, session: Session, test_card: Card):
        """Test bid/ask when no snapshot exists."""
        session.query(MarketSnapshot).filter(
            MarketSnapshot.card_id == test_card.id
        ).delete()
        session.commit()

        calc = PriceCalculator(session)
        spread = calc.calculate_bid_ask_spread(test_card.id)

        assert spread is None

    def test_bid_ask_no_bid(self, session: Session, test_card: Card, test_snapshot):
        """Test bid/ask when no bid exists."""
        test_snapshot.highest_bid = None
        session.add(test_snapshot)
        session.commit()

        calc = PriceCalculator(session)
        spread = calc.calculate_bid_ask_spread(test_card.id)

        assert spread is not None
        assert spread["highest_bid"] == 0
        assert spread["spread_amount"] == spread["lowest_ask"]


class TestPriceToSale:
    """Test price-to-sale ratio calculations."""

    def test_price_to_sale_ratio(self, session: Session, test_card: Card,
                                  test_prices, test_snapshot):
        """Test price-to-sale ratio calculation."""
        calc = PriceCalculator(session)
        ratio = calc.calculate_price_to_sale(test_card.id, period="30d")

        assert ratio is not None
        assert isinstance(ratio, float)
        assert ratio > 0

        # Ratio should be close to 1.0 if ask is near VWAP
        # From fixture: ask=28, VWAP~20, so ratio~1.4
        assert 1.0 < ratio < 2.0

    def test_price_to_sale_no_vwap(self, session: Session, test_card: Card, test_snapshot):
        """Test price-to-sale when no price data exists."""
        session.query(MarketPrice).filter(
            MarketPrice.card_id == test_card.id
        ).delete()
        session.commit()

        calc = PriceCalculator(session)
        ratio = calc.calculate_price_to_sale(test_card.id, period="30d")

        assert ratio is None

    def test_price_to_sale_no_ask(self, session: Session, test_card: Card, test_prices):
        """Test price-to-sale when no active listings exist."""
        session.query(MarketSnapshot).filter(
            MarketSnapshot.card_id == test_card.id
        ).delete()
        session.commit()

        calc = PriceCalculator(session)
        ratio = calc.calculate_price_to_sale(test_card.id, period="30d")

        assert ratio is None


class TestTimeSeries:
    """Test time-series data generation."""

    def test_time_series_single_card(self, session: Session, test_card: Card, test_prices):
        """Test time series for a single card."""
        calc = PriceCalculator(session)
        data = calc.get_time_series(
            card_id=test_card.id,
            interval="1d",
            period="30d"
        )

        assert isinstance(data, list)
        assert len(data) > 0

        # Check data structure
        for point in data:
            assert "date" in point
            assert "vwap" in point
            assert "floor" in point
            assert "ceiling" in point
            assert "volume" in point

            assert isinstance(point["volume"], int)
            assert point["floor"] <= point["vwap"] <= point["ceiling"]

    def test_time_series_product_type(self, session: Session, box_product):
        """Test time series for product type aggregate."""
        calc = PriceCalculator(session)
        data = calc.get_time_series(
            card_id=None,
            interval="1d",
            period="7d",
            product_type="Box"
        )

        assert isinstance(data, list)
        assert len(data) > 0

    def test_time_series_weekly_interval(self, session: Session, test_card: Card, test_prices):
        """Test time series with weekly interval."""
        calc = PriceCalculator(session)
        data = calc.get_time_series(
            card_id=test_card.id,
            interval="1w",
            period="30d"
        )

        assert isinstance(data, list)
        # Should have ~4 weeks of data
        assert 3 <= len(data) <= 5

    def test_time_series_no_data(self, session: Session, test_card: Card):
        """Test time series when no data exists."""
        session.query(MarketPrice).filter(
            MarketPrice.card_id == test_card.id
        ).delete()
        session.commit()

        calc = PriceCalculator(session)
        data = calc.get_time_series(
            card_id=test_card.id,
            interval="1d",
            period="7d"
        )

        assert isinstance(data, list)
        assert len(data) == 0


class TestComprehensiveMetrics:
    """Test comprehensive metrics aggregation."""

    def test_comprehensive_metrics(self, session: Session, test_card: Card,
                                    test_prices, test_snapshot):
        """Test getting all metrics at once."""
        calc = PriceCalculator(session)
        metrics = calc.get_comprehensive_metrics(test_card.id, period="30d")

        # Verify all metrics are present
        assert "vwap" in metrics
        assert "ema_7d" in metrics
        assert "ema_14d" in metrics
        assert "ema_30d" in metrics
        assert "price_delta_1d" in metrics
        assert "price_delta_7d" in metrics
        assert "price_delta_30d" in metrics
        assert "bid_ask_spread" in metrics
        assert "price_to_sale" in metrics

        # Verify VWAP is calculated
        assert metrics["vwap"] is not None
        assert metrics["vwap"] > 0

        # Verify EMAs are calculated
        assert metrics["ema_7d"] is not None
        assert metrics["ema_14d"] is not None

        # Verify price deltas are calculated
        assert metrics["price_delta_1d"] is not None
        assert metrics["price_delta_30d"] is not None

    def test_comprehensive_metrics_partial_data(self, session: Session, test_card: Card):
        """Test comprehensive metrics with partial data."""
        # Create minimal data
        now = datetime.utcnow()
        for i in range(3):
            price = MarketPrice(
                card_id=test_card.id,
                price=10.0 + i,
                title=f"Test {i}",
                sold_date=now - timedelta(days=2 - i),
                listing_type="sold",
                treatment="Classic Paper",
                platform="ebay",
                scraped_at=now
            )
            session.add(price)
        session.commit()

        calc = PriceCalculator(session)
        metrics = calc.get_comprehensive_metrics(test_card.id, period="7d")

        # VWAP should work
        assert metrics["vwap"] is not None

        # EMA might not work (insufficient data)
        # That's okay, should return None gracefully

        # Price delta might work
        # Depends on data distribution


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_time_period(self, session: Session, test_card: Card, test_prices):
        """Test with invalid time period."""
        calc = PriceCalculator(session)

        # Invalid period should return None for cutoff
        # But calculation should still work (treats as "all")
        vwap = calc.calculate_vwap(test_card.id, period="invalid")
        assert vwap is not None

    def test_zero_prices(self, session: Session, test_card: Card):
        """Test handling of zero prices."""
        now = datetime.utcnow()

        # Add some zero prices
        for i in range(5):
            price = MarketPrice(
                card_id=test_card.id,
                price=0.0,  # Zero price
                title=f"Zero {i}",
                sold_date=now - timedelta(days=4 - i),
                listing_type="sold",
                treatment="Classic Paper",
                platform="ebay",
                scraped_at=now
            )
            session.add(price)
        session.commit()

        calc = PriceCalculator(session)
        vwap = calc.calculate_vwap(test_card.id, period="7d")

        # Should exclude zero prices
        assert vwap is None  # All prices were zero

    def test_single_data_point(self, session: Session, test_card: Card):
        """Test with only one data point."""
        now = datetime.utcnow()
        price = MarketPrice(
            card_id=test_card.id,
            price=10.0,
            title="Single",
            sold_date=now,
            listing_type="sold",
            treatment="Classic Paper",
            platform="ebay",
            scraped_at=now
        )
        session.add(price)
        session.commit()

        calc = PriceCalculator(session)

        # VWAP should work with one point
        vwap = calc.calculate_vwap(test_card.id, period="7d")
        assert vwap == 10.0

        # Delta should fail (need before/after)
        delta = calc.calculate_price_delta(test_card.id, period="7d")
        assert delta is None

        # EMA should fail (need window points)
        ema = calc.calculate_ema(test_card.id, period="7d", window=7)
        assert ema is None
