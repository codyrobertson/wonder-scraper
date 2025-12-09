#!/usr/bin/env python3
"""
Generate seller pricing analysis report: How accurately do sellers price their items?

This report analyzes the VARIANCE in seller pricing for identical items (same card + treatment),
revealing how much "gut feeling" pricing differs from market reality.

Key insight: When the same exact item sells for $20 one day and $200 the next,
someone is wildly mispricing - either leaving money on the table or overcharging.

Usage:
    python scripts/generate_pricing_analysis.py
    python scripts/generate_pricing_analysis.py --days 30
    python scripts/generate_pricing_analysis.py --print
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

from sqlmodel import Session
from sqlalchemy import text

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import engine


def format_currency(val: float) -> str:
    """Format value as currency."""
    if val is None:
        return "N/A"
    return f"${val:,.2f}"


def format_pct(val: float) -> str:
    """Format as percentage."""
    if val is None:
        return "N/A"
    return f"{val:.1f}%"


def format_pct_change(val: float) -> str:
    """Format as percentage change with +/- sign."""
    if val is None:
        return "N/A"
    if val > 0:
        return f"+{val:.0f}%"
    return f"{val:.0f}%"


def bar_txt(value: float, max_value: float, width: int = 25, filled: str = "█", empty: str = "░") -> str:
    """Create ASCII bar for txt output."""
    if max_value == 0:
        return empty * width
    fill_count = int((value / max_value) * width)
    return filled * fill_count + empty * (width - fill_count)


def generate_pricing_analysis(days: int = 90) -> dict:
    """
    Analyze seller pricing accuracy by examining price variance for identical items.

    METHODOLOGY:
    - Compare sales of the SAME card + SAME treatment to each other
    - Calculate price spread, variance, and outliers within each group
    - Show how "gut feeling" pricing creates massive price disparities
    - Compare current asking prices to recent actual sale prices
    """
    with Session(engine) as session:
        now = datetime.utcnow()
        period_start = now - timedelta(days=days)

        data = {
            "generated_at": now,
            "period_start": period_start,
            "period_end": now,
            "days": days,
        }

        # Get data quality stats
        quality_stats = session.execute(text("""
            SELECT
                COUNT(*) as total_sold,
                COUNT(CASE WHEN treatment IS NOT NULL AND treatment != '' THEN 1 END) as has_treatment,
                COUNT(CASE WHEN seller_name IS NOT NULL AND seller_name != '' THEN 1 END) as has_seller,
                COUNT(DISTINCT card_id) as unique_cards
            FROM marketprice
            WHERE listing_type = 'sold'
            AND sold_date >= :start
            AND platform = 'ebay'
        """), {"start": period_start}).first()

        data["data_quality"] = {
            "total_sales": quality_stats[0],
            "with_treatment": quality_stats[1],
            "treatment_coverage": (quality_stats[1] / quality_stats[0] * 100) if quality_stats[0] > 0 else 0,
            "with_seller": quality_stats[2],
            "seller_coverage": (quality_stats[2] / quality_stats[0] * 100) if quality_stats[0] > 0 else 0,
            "unique_cards": quality_stats[3],
        }

        # PRICE VARIANCE ANALYSIS - The core story
        # How much do prices vary for the SAME item?
        variance_stats = session.execute(text("""
            WITH sale_stats AS (
                SELECT
                    mp.card_id,
                    mp.treatment,
                    c.name,
                    c.product_type,
                    COUNT(*) as sales,
                    MIN(mp.price) as min_price,
                    MAX(mp.price) as max_price,
                    AVG(mp.price) as avg_price,
                    STDDEV(mp.price) as price_stddev,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mp.price) as median_price
                FROM marketprice mp
                JOIN card c ON mp.card_id = c.id
                WHERE mp.listing_type = 'sold'
                AND mp.platform = 'ebay'
                AND mp.sold_date >= :start
                AND mp.treatment IS NOT NULL
                AND mp.treatment != ''
                GROUP BY mp.card_id, mp.treatment, c.name, c.product_type
                HAVING COUNT(*) >= 3
            )
            SELECT
                COUNT(*) as items_analyzed,
                AVG((max_price - min_price) / NULLIF(avg_price, 0) * 100) as avg_spread_pct,
                COUNT(CASE WHEN (max_price - min_price) / NULLIF(avg_price, 0) >= 1.0 THEN 1 END) as items_100pct_spread,
                COUNT(CASE WHEN (max_price - min_price) / NULLIF(avg_price, 0) >= 0.5 THEN 1 END) as items_50pct_spread,
                MAX((max_price - min_price) / NULLIF(avg_price, 0) * 100) as max_spread_pct
            FROM sale_stats
        """), {"start": period_start}).first()

        data["variance_summary"] = {
            "items_analyzed": variance_stats[0] or 0,
            "avg_spread_pct": variance_stats[1] or 0,
            "items_100pct_spread": variance_stats[2] or 0,
            "items_50pct_spread": variance_stats[3] or 0,
            "max_spread_pct": variance_stats[4] or 0,
        }

        # WORST PRICING - Items with highest price variance (same card+treatment)
        worst_pricing = session.execute(text("""
            WITH sale_stats AS (
                SELECT
                    mp.card_id,
                    mp.treatment,
                    c.name,
                    c.product_type,
                    COUNT(*) as sales,
                    MIN(mp.price) as min_price,
                    MAX(mp.price) as max_price,
                    AVG(mp.price) as avg_price,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY mp.price) as median_price,
                    (MAX(mp.price) - MIN(mp.price)) / NULLIF(AVG(mp.price), 0) * 100 as spread_pct
                FROM marketprice mp
                JOIN card c ON mp.card_id = c.id
                WHERE mp.listing_type = 'sold'
                AND mp.platform = 'ebay'
                AND mp.sold_date >= :start
                AND mp.treatment IS NOT NULL
                AND mp.treatment != ''
                GROUP BY mp.card_id, mp.treatment, c.name, c.product_type
                HAVING COUNT(*) >= 3
            )
            SELECT name, treatment, product_type, sales, min_price, max_price, avg_price, median_price, spread_pct
            FROM sale_stats
            ORDER BY spread_pct DESC
            LIMIT 20
        """), {"start": period_start}).all()

        data["worst_pricing"] = [
            {
                "name": row[0],
                "treatment": row[1],
                "product_type": row[2],
                "sales": row[3],
                "min_price": row[4],
                "max_price": row[5],
                "avg_price": row[6],
                "median_price": float(row[7]) if row[7] else row[6],
                "spread_pct": row[8],
            }
            for row in worst_pricing
        ]

        # OUTLIER SALES - Individual sales way above/below median for that item
        outliers = session.execute(text("""
            WITH item_medians AS (
                SELECT
                    card_id,
                    treatment,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
                    COUNT(*) as sale_count
                FROM marketprice
                WHERE listing_type = 'sold'
                AND platform = 'ebay'
                AND sold_date >= :start
                AND treatment IS NOT NULL
                AND treatment != ''
                GROUP BY card_id, treatment
                HAVING COUNT(*) >= 3
            )
            SELECT
                c.name,
                mp.treatment,
                mp.price as sold_price,
                im.median_price,
                (mp.price - im.median_price) / NULLIF(im.median_price, 0) * 100 as deviation_pct,
                mp.sold_date,
                mp.seller_name,
                im.sale_count,
                CASE
                    WHEN mp.price > im.median_price THEN 'overpaid'
                    ELSE 'underpaid'
                END as direction
            FROM marketprice mp
            JOIN card c ON mp.card_id = c.id
            JOIN item_medians im ON mp.card_id = im.card_id AND mp.treatment = im.treatment
            WHERE mp.listing_type = 'sold'
            AND mp.sold_date >= :start
            AND mp.treatment IS NOT NULL
            AND mp.treatment != ''
            AND im.median_price > 0
            AND ABS((mp.price - im.median_price) / im.median_price) >= 0.5
            ORDER BY ABS((mp.price - im.median_price) / im.median_price) DESC
            LIMIT 30
        """), {"start": period_start}).all()

        data["outliers"] = [
            {
                "name": row[0],
                "treatment": row[1],
                "sold_price": row[2],
                "median": float(row[3]) if row[3] else 0,
                "deviation_pct": row[4],
                "date": row[5],
                "seller": row[6],
                "sample_size": row[7],
                "direction": row[8],
            }
            for row in outliers
        ]

        # CURRENT LISTINGS VS REALITY - Are today's sellers pricing accurately?
        current_vs_reality = session.execute(text("""
            WITH recent_sales AS (
                SELECT
                    card_id,
                    treatment,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_sold,
                    AVG(price) as avg_sold,
                    COUNT(*) as sale_count
                FROM marketprice
                WHERE listing_type = 'sold'
                AND platform = 'ebay'
                AND sold_date >= NOW() - INTERVAL '30 days'
                AND treatment IS NOT NULL
                AND treatment != ''
                GROUP BY card_id, treatment
                HAVING COUNT(*) >= 2
            ),
            current_listings AS (
                SELECT
                    card_id,
                    treatment,
                    MIN(price) as floor_price,
                    AVG(price) as avg_ask,
                    COUNT(*) as listing_count
                FROM marketprice
                WHERE listing_type = 'active'
                AND platform = 'ebay'
                AND treatment IS NOT NULL
                AND treatment != ''
                GROUP BY card_id, treatment
            )
            SELECT
                c.name,
                rs.treatment,
                rs.sale_count,
                rs.median_sold,
                rs.avg_sold,
                cl.floor_price,
                cl.avg_ask,
                cl.listing_count,
                (cl.floor_price - rs.median_sold) / NULLIF(rs.median_sold, 0) * 100 as floor_gap_pct,
                (cl.avg_ask - rs.avg_sold) / NULLIF(rs.avg_sold, 0) * 100 as avg_gap_pct
            FROM recent_sales rs
            JOIN current_listings cl ON rs.card_id = cl.card_id AND rs.treatment = cl.treatment
            JOIN card c ON rs.card_id = c.id
            WHERE cl.floor_price > 0 AND rs.median_sold > 0
            ORDER BY ABS((cl.floor_price - rs.median_sold) / NULLIF(rs.median_sold, 0) * 100) DESC
            LIMIT 20
        """)).all()

        data["current_vs_reality"] = [
            {
                "name": row[0],
                "treatment": row[1],
                "recent_sales": row[2],
                "median_sold": float(row[3]) if row[3] else 0,
                "avg_sold": row[4],
                "floor_price": row[5],
                "avg_ask": row[6],
                "listing_count": row[7],
                "floor_gap_pct": row[8],
                "avg_gap_pct": row[9],
            }
            for row in current_vs_reality
        ]

        # VARIANCE BY TREATMENT TYPE
        by_treatment = session.execute(text("""
            WITH sale_stats AS (
                SELECT
                    mp.treatment,
                    mp.card_id,
                    COUNT(*) as sales,
                    MIN(mp.price) as min_price,
                    MAX(mp.price) as max_price,
                    AVG(mp.price) as avg_price
                FROM marketprice mp
                WHERE mp.listing_type = 'sold'
                AND mp.platform = 'ebay'
                AND mp.sold_date >= :start
                AND mp.treatment IS NOT NULL
                AND mp.treatment != ''
                GROUP BY mp.treatment, mp.card_id
                HAVING COUNT(*) >= 2
            )
            SELECT
                treatment,
                COUNT(DISTINCT card_id) as unique_items,
                SUM(sales) as total_sales,
                AVG((max_price - min_price) / NULLIF(avg_price, 0) * 100) as avg_spread_pct,
                COUNT(CASE WHEN (max_price - min_price) / NULLIF(avg_price, 0) >= 1.0 THEN 1 END) as items_100pct_spread
            FROM sale_stats
            GROUP BY treatment
            ORDER BY SUM(sales) DESC
        """), {"start": period_start}).all()

        data["by_treatment"] = [
            {
                "treatment": row[0],
                "unique_items": row[1],
                "total_sales": row[2],
                "avg_spread_pct": row[3] if row[3] else 0,
                "items_100pct_spread": row[4] or 0,
            }
            for row in by_treatment
        ]

        # VARIANCE BY PRODUCT TYPE
        by_type = session.execute(text("""
            WITH sale_stats AS (
                SELECT
                    c.product_type,
                    mp.card_id,
                    mp.treatment,
                    COUNT(*) as sales,
                    MIN(mp.price) as min_price,
                    MAX(mp.price) as max_price,
                    AVG(mp.price) as avg_price
                FROM marketprice mp
                JOIN card c ON mp.card_id = c.id
                WHERE mp.listing_type = 'sold'
                AND mp.platform = 'ebay'
                AND mp.sold_date >= :start
                AND mp.treatment IS NOT NULL
                AND mp.treatment != ''
                GROUP BY c.product_type, mp.card_id, mp.treatment
                HAVING COUNT(*) >= 2
            )
            SELECT
                product_type,
                COUNT(*) as unique_items,
                SUM(sales) as total_sales,
                AVG((max_price - min_price) / NULLIF(avg_price, 0) * 100) as avg_spread_pct,
                COUNT(CASE WHEN (max_price - min_price) / NULLIF(avg_price, 0) >= 1.0 THEN 1 END) as items_100pct_spread
            FROM sale_stats
            GROUP BY product_type
            ORDER BY SUM(sales) DESC
        """), {"start": period_start}).all()

        data["by_product_type"] = [
            {
                "type": row[0],
                "unique_items": row[1],
                "total_sales": row[2],
                "avg_spread_pct": row[3] if row[3] else 0,
                "items_100pct_spread": row[4] or 0,
            }
            for row in by_type
        ]

        # MONEY LEFT ON TABLE - Sales significantly below median (seller underpriced)
        money_left = session.execute(text("""
            WITH item_medians AS (
                SELECT
                    card_id,
                    treatment,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
                    COUNT(*) as sale_count
                FROM marketprice
                WHERE listing_type = 'sold'
                AND platform = 'ebay'
                AND sold_date >= :start
                AND treatment IS NOT NULL
                AND treatment != ''
                GROUP BY card_id, treatment
                HAVING COUNT(*) >= 3
            )
            SELECT
                SUM(im.median_price - mp.price) as total_left_on_table,
                COUNT(*) as underprice_count,
                AVG((im.median_price - mp.price) / NULLIF(im.median_price, 0) * 100) as avg_underprice_pct
            FROM marketprice mp
            JOIN item_medians im ON mp.card_id = im.card_id AND mp.treatment = im.treatment
            WHERE mp.listing_type = 'sold'
            AND mp.sold_date >= :start
            AND mp.treatment IS NOT NULL
            AND mp.treatment != ''
            AND mp.price < im.median_price * 0.7
            AND im.median_price > 5
        """), {"start": period_start}).first()

        data["money_left_on_table"] = {
            "total_amount": money_left[0] or 0,
            "transaction_count": money_left[1] or 0,
            "avg_underprice_pct": money_left[2] or 0,
        }

        # OVERPAY ANALYSIS - Sales significantly above median (buyer overpaid)
        overpay = session.execute(text("""
            WITH item_medians AS (
                SELECT
                    card_id,
                    treatment,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
                    COUNT(*) as sale_count
                FROM marketprice
                WHERE listing_type = 'sold'
                AND platform = 'ebay'
                AND sold_date >= :start
                AND treatment IS NOT NULL
                AND treatment != ''
                GROUP BY card_id, treatment
                HAVING COUNT(*) >= 3
            )
            SELECT
                SUM(mp.price - im.median_price) as total_overpaid,
                COUNT(*) as overpay_count,
                AVG((mp.price - im.median_price) / NULLIF(im.median_price, 0) * 100) as avg_overpay_pct
            FROM marketprice mp
            JOIN item_medians im ON mp.card_id = im.card_id AND mp.treatment = im.treatment
            WHERE mp.listing_type = 'sold'
            AND mp.sold_date >= :start
            AND mp.treatment IS NOT NULL
            AND mp.treatment != ''
            AND mp.price > im.median_price * 1.5
            AND im.median_price > 5
        """), {"start": period_start}).first()

        data["overpay_analysis"] = {
            "total_amount": overpay[0] or 0,
            "transaction_count": overpay[1] or 0,
            "avg_overpay_pct": overpay[2] or 0,
        }

        return data


def generate_txt_report(data: dict) -> str:
    """Generate plain text pricing analysis report."""
    lines = []

    # Header
    lines.append("")
    lines.append("+" + "=" * 78 + "+")
    lines.append("|" + "  WONDERS OF THE FIRST - EBAY PRICING ANALYSIS  ".center(78) + "|")
    lines.append("|" + f"  {data['period_start'].strftime('%b %d')} - {data['period_end'].strftime('%b %d, %Y')} ({data['days']} days)  ".center(78) + "|")
    lines.append("+" + "=" * 78 + "+")

    # Methodology
    lines.append("")
    lines.append("=" * 80)
    lines.append("  METHODOLOGY")
    lines.append("=" * 80)
    lines.append("  This analysis uses TREATMENT-MATCHED comparisons:")
    lines.append("  - Floor Price = Minimum active eBay listing for SAME card + SAME treatment")
    lines.append("  - Example: A 'Phoenix Quill (Formless Foil)' sale is compared ONLY to")
    lines.append("    other 'Phoenix Quill (Formless Foil)' active listings, not Paper/OCM/etc.")
    lines.append("  - Sales without treatment data are excluded from this analysis")
    lines.append("")
    lines.append("  DEFINITIONS:")
    lines.append("  - 'Below Floor' = Sold price < lowest active listing (same card+treatment)")
    lines.append("  - 'X% below' = Sold for X% less than the floor price")

    # Data Quality
    dq = data["data_quality"]
    lines.append("")
    lines.append("=" * 80)
    lines.append("  DATA QUALITY")
    lines.append("=" * 80)
    lines.append(f"  Total eBay Sales (period):     {dq['total_sales']:,}")
    lines.append(f"  Sales with Treatment Data:     {dq['with_treatment']:,} ({dq['treatment_coverage']:.1f}%)")
    lines.append(f"  Sales with Seller Data:        {dq['with_seller']:,} ({dq['seller_coverage']:.1f}%)")
    lines.append(f"  Unique Cards Sold:             {dq['unique_cards']:,}")
    if dq['treatment_coverage'] < 80:
        lines.append("")
        lines.append(f"  NOTE: {100-dq['treatment_coverage']:.0f}% of sales lack treatment data and are excluded.")

    # Main Treatment-Matched Analysis
    tm = data["treatment_matched_analysis"]
    lines.append("")
    lines.append("=" * 80)
    lines.append("  TREATMENT-MATCHED FLOOR ANALYSIS")
    lines.append("=" * 80)
    lines.append(f"  Sales Analyzed:              {tm['total_sales']:,}")
    lines.append(f"  Sales Below Floor:           {tm['below_floor']:,} ({tm['below_floor_pct']:.1f}%)")
    lines.append("")
    lines.append("  BY DISCOUNT DEPTH:")
    lines.append(f"    Any amount below floor:    {tm['below_floor']:,} sales  ({tm['below_floor_pct']:.1f}%)")
    lines.append(f"    10%+ below floor:          {tm['below_10pct']:,} sales  ({tm['below_10pct_rate']:.1f}%)")
    lines.append(f"    20%+ below floor:          {tm['below_20pct']:,} sales  ({tm['below_20pct_rate']:.1f}%)")
    lines.append(f"    30%+ below floor:          {tm['below_30pct']:,} sales  ({tm['below_30pct_rate']:.1f}%)")
    lines.append(f"    50%+ below floor:          {tm['below_50pct']:,} sales  ({tm['below_50pct_rate']:.1f}%)")
    lines.append("")
    lines.append(f"  Average Sale Price:          {format_currency(tm['avg_sale_price'])}")
    lines.append(f"  Average Floor Price:         {format_currency(tm['avg_floor_price'])}")

    # Distribution chart
    if data["floor_distribution"]:
        lines.append("")
        lines.append("=" * 80)
        lines.append("  PRICE DISTRIBUTION (vs Treatment-Matched Floor)")
        lines.append("=" * 80)
        max_count = max(d["count"] for d in data["floor_distribution"]) if data["floor_distribution"] else 1
        total = sum(d["count"] for d in data["floor_distribution"])
        for d in data["floor_distribution"]:
            pct = (d["count"] / total * 100) if total > 0 else 0
            lines.append(f"  {d['bucket']:14} | {bar_txt(d['count'], max_count, 30)} | {d['count']:4} ({pct:5.1f}%)")

    # By Treatment
    if data["by_treatment"]:
        lines.append("")
        lines.append("=" * 80)
        lines.append("  ANALYSIS BY TREATMENT (10+ sales minimum)")
        lines.append("=" * 80)
        lines.append(f"  {'Treatment':<18} | {'Sales':>6} | {'<Floor':>6} | {'Rate':>7} | {'Avg Sale':>10} | {'Avg Floor':>10}")
        lines.append("  " + "-" * 75)
        for t in data["by_treatment"]:
            lines.append(f"  {t['treatment'][:18]:<18} | {t['total']:>6} | {t['below_floor']:>6} | {t['below_floor_pct']:>6.1f}% | {format_currency(t['avg_sale']):>10} | {format_currency(t['avg_floor']):>10}")

    # By product type
    if data["by_product_type"]:
        lines.append("")
        lines.append("=" * 80)
        lines.append("  BY PRODUCT TYPE")
        lines.append("=" * 80)
        lines.append(f"  {'Type':<10} | {'Sales':>6} | {'<Floor':>6} | {'Rate':>7} | {'Avg Sale':>10} | {'Avg Floor':>10}")
        lines.append("  " + "-" * 60)
        for t in data["by_product_type"]:
            lines.append(f"  {(t['type'] or 'Unknown'):<10} | {t['total']:>6} | {t['below_floor']:>6} | {t['below_floor_pct']:>6.1f}% | {format_currency(t['avg_sale']):>10} | {format_currency(t['avg_floor']):>10}")

    # Cards with repeat below-floor sales
    if data["repeat_below_floor"]:
        lines.append("")
        lines.append("=" * 80)
        lines.append("  CARDS WITH REPEAT BELOW-FLOOR SALES (2+ occurrences)")
        lines.append("=" * 80)
        for i, c in enumerate(data["repeat_below_floor"][:12], 1):
            name_treat = f"{c['name'][:35]} ({c['treatment']})"
            lines.append(f"  {i:2}. {name_treat}")
            lines.append(f"      {c['below_floor']}x below floor out of {c['total_sales']} sales | Floor: {format_currency(c['floor'])} | Avg Sold: {format_currency(c['avg_sold'])} ({c['avg_discount']:.0f}% below)")

    # Best individual deals
    if data["best_deals"]:
        lines.append("")
        lines.append("=" * 80)
        lines.append("  NOTABLE BELOW-FLOOR SALES (30%+ discount, 2+ active listings)")
        lines.append("=" * 80)
        lines.append("  [Date]  Card (Treatment)                                    Sold      Floor   Disc")
        lines.append("  " + "-" * 78)
        for d in data["best_deals"][:15]:
            name_treat = f"{d['name'][:30]} ({d['treatment']})"
            date_str = d["date"].strftime("%m/%d") if d["date"] else "N/A"
            lines.append(f"  [{date_str}] {name_treat:<50} {format_currency(d['sold_price']):>8} {format_currency(d['floor']):>9} {d['discount']:>4.0f}%")

    # Summary observations (factual only)
    lines.append("")
    lines.append("=" * 80)
    lines.append("  SUMMARY")
    lines.append("=" * 80)
    tm = data["treatment_matched_analysis"]
    lines.append(f"  - {tm['below_floor_pct']:.1f}% of treatment-matched sales occurred below the current floor")
    lines.append(f"  - {tm['below_20pct_rate']:.1f}% sold at 20%+ below floor")
    if data["by_treatment"]:
        highest = max(data["by_treatment"], key=lambda x: x["below_floor_pct"])
        lowest = min(data["by_treatment"], key=lambda x: x["below_floor_pct"])
        lines.append(f"  - Highest below-floor rate: {highest['treatment']} ({highest['below_floor_pct']:.1f}%)")
        lines.append(f"  - Lowest below-floor rate: {lowest['treatment']} ({lowest['below_floor_pct']:.1f}%)")

    # Footer
    lines.append("")
    lines.append("-" * 80)
    lines.append(f"  Generated: {data['generated_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("  Data Source: eBay sold listings via WondersTrader.com")
    lines.append("-" * 80)
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate eBay pricing analysis report")
    parser.add_argument("--days", "-d", type=int, default=90, help="Days to analyze (default: 90)")
    parser.add_argument("--output", "-o", default="data/marketReports", help="Output directory")
    parser.add_argument("--print", "-p", action="store_true", help="Print report to terminal")

    args = parser.parse_args()

    print(f"Generating pricing analysis for last {args.days} days...")

    data = generate_pricing_analysis(args.days)

    # Create output directory
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate and save
    report = generate_txt_report(data)
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    output_path = output_dir / f"{date_str}-pricing-analysis.txt"
    output_path.write_text(report)

    print(f"Saved: {output_path}")

    if args.print:
        print(report)

    # Print summary
    tm = data["treatment_matched_analysis"]
    print(f"\nSummary (Treatment-Matched):")
    print(f"  Total Sales: {tm['total_sales']:,}")
    print(f"  Below Floor: {tm['below_floor']:,} ({tm['below_floor_pct']:.1f}%)")
    print(f"  20%+ Below:  {tm['below_20pct']:,} ({tm['below_20pct_rate']:.1f}%)")


if __name__ == "__main__":
    main()
