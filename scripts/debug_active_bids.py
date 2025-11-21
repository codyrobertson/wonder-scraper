import asyncio
from app.scraper.browser import BrowserManager, get_page_content
from bs4 import BeautifulSoup
import re

async def debug_active_bids():
    print("Fetching active listings for 'The First'...")
    # Use a broad query to ensure we find auctions
    # Add auction filter
    url = "https://www.ebay.com/sch/i.html?_nkw=The+First+Wonders+of+the+First&LH_Auction=1" 
    
    await BrowserManager.get_browser()
    try:
        html = await get_page_content(url)
        
        if "s-item" in html:
             print("Confirmed 's-item' string exists in HTML payload.")
        else:
             print("WARNING: 's-item' string NOT found in HTML payload.")

        # Save HTML for inspection
        with open("active_debug.html", "w") as f:
            f.write(html)
        print("Saved active_debug.html")
        
        soup = BeautifulSoup(html, "lxml")
        
        # Try finding items with both classes
        items = soup.select("li.s-item, div.s-item, li.s-card, div.s-card, .s-item, .s-card")
        print(f"Found {len(items)} items (mixed selectors).")

        for i, item in enumerate(items[:5]):
            print(f"\n--- Item {i+1} ---")
            # Determine class for logging
            classes = item.get("class", [])
            print(f"Classes: {classes}")
            
            if "s-item__header" in classes or "s-card__header" in classes:
                 print("Skipping header")
                 continue

            # Dump full text
            full_text = item.get_text(" | ", strip=True)
            print(f"Full Text: {full_text}")
            
            # Inspect structure
            print("Children classes:")
            for child in item.find_all(True):
                if child.get("class"):
                    print(f"  {child.name}: {child.get('class')}")

            title = item.select_one(".s-item__title, .s-card__title")
            print(f"Title: {title.get_text(strip=True) if title else 'None'}")
            
            # Debug Bid Selectors
            bid_elem = item.select_one(".s-item__bidCount, .s-item__bids, .s-item__details .s-item__bidCount, .s-item__bid-count, .s-card__bidCount, .s-card__bids")
            print(f"Bid Elem Text: {bid_elem.get_text(strip=True) if bid_elem else 'None'}")
            
            # Check for price too
            price = item.select_one(".s-item__price, .s-card__price")
            print(f"Price: {price.get_text(strip=True) if price else 'None'}")

            
    finally:
        await BrowserManager.close()

if __name__ == "__main__":
    asyncio.run(debug_active_bids())

