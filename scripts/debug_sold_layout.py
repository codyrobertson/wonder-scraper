import asyncio
from app.scraper.browser import BrowserManager, get_page_content
from bs4 import BeautifulSoup

async def debug_sold_layout():
    print("Fetching SOLD listings for 'Aerius of Thalwind'...")
    # Use the exact URL pattern used in the app for sold listings
    # LH_Sold=1, LH_Complete=1
    url = "https://www.ebay.com/sch/i.html?_nkw=Aerius+of+Thalwind+Existence+Wonders+of+the+First&_sacat=183454&LH_Sold=1&LH_Complete=1"
    
    await BrowserManager.get_browser()
    try:
        html = await get_page_content(url)
        
        with open("sold_debug.html", "w") as f:
            f.write(html)
        print("Saved sold_debug.html")
        
        soup = BeautifulSoup(html, "lxml")
        items = soup.select("li.s-item, div.s-item, li.s-card, div.s-card, .s-item, .s-card")
        print(f"Found {len(items)} items.")
        
        for i, item in enumerate(items[:5]):
            print(f"\n--- Item {i+1} ---")
            classes = item.get("class", [])
            print(f"Classes: {classes}")
            
            if "s-item__header" in classes or "s-card__header" in classes:
                 continue

            title = item.select_one(".s-item__title, .s-card__title")
            print(f"Title: {title.get_text(strip=True) if title else 'None'}")
            
            # Dump full text to find the date
            full_text = item.get_text(" | ", strip=True)
            print(f"Full Text: {full_text}")
            
            # Check for existing date selectors
            caption = item.select_one(".s-item__caption, .s-card__caption")
            print(f"Caption: {caption.get_text(strip=True) if caption else 'None'}")
            
            tag = item.select_one(".s-item__title--tag")
            print(f"Tag: {tag.get_text(strip=True) if tag else 'None'}")

    finally:
        await BrowserManager.close()

if __name__ == "__main__":
    asyncio.run(debug_sold_layout())
