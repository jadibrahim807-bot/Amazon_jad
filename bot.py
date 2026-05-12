import os, requests, time

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def get_deals():
    url = "https://api.keepa.com/deal"
    params = {
        "key": KEEPA_API_KEY,
        "selection": '{"categories":[16310101],"deltaPercent":20,"deltaPercentInInterval":20,"salesRankPercentInInterval":50,"priceTypes":[0],"dateRange":1,"isLowest":true,"isLowestOffer":false,"isOutOfStock":false,"titleSearch":"","minRating":0,"isRangeEnabled":false,"isFilterEnabled":false,"filterErotic":true,"sortType":0,"page":0,"domainId":1}'
    }
    r = requests.get(url, params=params)
    return r.json()

def calculate_fbm_profit(price):
    price_usd = price / 100
    shipping = 5.00
    amazon_fee = price_usd * 0.15
    profit = price_usd - shipping - amazon_fee
    roi = (profit / shipping) * 100
    return round(profit, 2), round(roi, 1)

def main():
    send_telegram("🤖 <b>Amazon FBM Bot Started!</b>\nSearching for profitable deals...")
    while True:
        try:
            data = get_deals()
            deals = data.get("deals", {}).get("dr", [])
            found = 0
            for deal in deals[:10]:
                try:
                    asin = deal.get("asin", "")
                    title = deal.get("title", "Unknown")[:60]
                    price = deal.get("current", [0])[0]
                    if price <= 0:
                        continue
                    price_usd = price / 100
                    if price_usd < 10 or price_usd > 100:
                        continue
                    profit, roi = calculate_fbm_profit(price)
                    if roi < 15:
                        continue
                    msg = (
                        f"✅ <b>FBM Deal Found!</b>\n\n"
                        f"🛍 <b>{title}</b>\n"
                        f"📦 ASIN: <code>{asin}</code>\n"
                        f"🔗 https://amazon.com/dp/{asin}\n"
                        f"💰 Price: ${price_usd:.2f}\n"
                        f"💵 FBM Profit: ${profit}\n"
                        f"📈 ROI: {roi}%"
                    )
                    send_telegram(msg)
                    found += 1
                    time.sleep(2)
                except:
                    continue
            if found == 0:
                send_telegram("🔍 No deals found this round, retrying in 1 hour...")
        except Exception as e:
            send_telegram(f"❌ Error: {e}")
        time.sleep(3600)

if __name__ == "__main__":
    main()

