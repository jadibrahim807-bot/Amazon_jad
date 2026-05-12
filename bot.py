import os, requests, time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
SP_CLIENT_ID = os.environ.get("SP_CLIENT_ID")
SP_CLIENT_SECRET = os.environ.get("SP_CLIENT_SECRET")
SP_REFRESH_TOKEN = os.environ.get("SP_REFRESH_TOKEN")

MARKETPLACE_ID = "ATVPDKIKX0DER"  # Amazon.com

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def get_sp_access_token():
    r = requests.post("https://api.amazon.com/auth/o2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": SP_REFRESH_TOKEN,
        "client_id": SP_CLIENT_ID,
        "client_secret": SP_CLIENT_SECRET,
    })
    return r.json().get("access_token")

def get_best_sellers(access_token, category="grocery"):
    headers = {
        "x-amz-access-token": access_token,
        "x-amz-date": datetime.utcnow().strftime("%Y%m%dT%H%M%SZ"),
    }
    url = f"https://sellingpartnerapi-na.amazon.com/catalog/2022-04-01/items"
    params = {
        "marketplaceIds": MARKETPLACE_ID,
        "keywords": category,
        "includedData": "summaries,salesRanks,offers",
    }
    r = requests.get(url, headers=headers, params=params)
    return r.json().get("items", [])

def calculate_fbm_profit(price):
    shipping_cost = 5.00
    amazon_fee = price * 0.15
    profit = price - shipping_cost - amazon_fee
    roi = (profit / shipping_cost) * 100 if shipping_cost > 0 else 0
    return round(profit, 2), round(roi, 1)

def process_products(items):
    results = []
    for item in items:
        try:
            summaries = item.get("summaries", [{}])[0]
            title = summaries.get("itemName", "Unknown")
            asin = item.get("asin", "")
            offers = item.get("offers", [{}])
            if not offers:
                continue
            price = float(offers[0].get("price", {}).get("amount", 0))
            if price < 10 or price > 100:
                continue
            profit, roi = calculate_fbm_profit(price)
            if roi < 20:
                continue
            results.append({
                "title": title,
                "asin": asin,
                "price": price,
                "profit": profit,
                "roi": roi,
            })
        except:
            continue
    return results

def main():
    send_telegram("🤖 <b>Amazon FBM Bot Started!</b>\nSearching for profitable products...")
    categories = ["grocery", "home", "kitchen", "beauty"]
    while True:
        try:
            token = get_sp_access_token()
            if not token:
                send_telegram("❌ SP-API auth failed, check credentials")
                time.sleep(3600)
                continue
            found = 0
            for cat in categories:
                items = get_best_sellers(token, cat)
                products = process_products(items)
                for p in products:
                    msg = (
                        f"✅ <b>FBM Deal Found!</b>\n\n"
                        f"🛍 <b>{p['title'][:60]}</b>\n"
                        f"📦 ASIN: <code>{p['asin']}</code>\n"
                        f"🔗 https://amazon.com/dp/{p['asin']}\n"
                        f"💰 Price: ${p['price']}\n"
                        f"💵 FBM Profit: ${p['profit']}\n"
                        f"📈 ROI: {p['roi']}%"
                    )
                    send_telegram(msg)
                    found += 1
                    time.sleep(2)
            if found == 0:
                send_telegram("🔍 No deals found this round, retrying in 1 hour...")
        except Exception as e:
            send_telegram(f"❌ Error: {e}")
        time.sleep(3600)

if __name__ == "__main__":
    main()
