import os, requests, time, json

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")

DOMAINS = {"🇺🇸 USA": 1, "🇨🇦 Canada": 6}

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}, timeout=10)
    except:
        pass

def get_deals(domain_id):
    url = "https://api.keepa.com/deal"
    params = {
        "key": KEEPA_API_KEY,
        "selection": json.dumps({
            "deltaPercent": 20,
            "priceTypes": [0],
            "dateRange": 1,
            "isLowest": True,
            "isOutOfStock": False,
            "filterErotic": True,
            "sortType": 4,
            "page": 0,
            "domainId": domain_id
        })
    }
    r = requests.get(url, params=params, timeout=15)
    return r.json()

def calculate_profit(price_usd, domain):
    if domain == 1:
        shipping = 4.50
        currency = "$"
    else:
        shipping = 6.00
        currency = "CA$"
    amazon_fee = price_usd * 0.15
    profit = price_usd - shipping - amazon_fee
    roi = (profit / (price_usd * 0.5)) * 100
    return round(profit, 2), round(roi, 1), currency

def main():
    send_telegram("🚀 <b>Amazon FBM Bot Started!</b>\n🇺🇸 USA + 🇨🇦 Canada\nSearching for hot deals...")
    
    while True:
        try:
            total_found = 0
            for country, domain_id in DOMAINS.items():
                try:
                    data = get_deals(domain_id)
                    deals = data.get("deals", {}).get("dr", [])
                    
                    for deal in deals[:30]:
                        try:
                            asin = deal.get("asin", "")
                            title = deal.get("title", "Unknown")[:70]
                            current = deal.get("current", [0])
                            
                            if not current or current[0] <= 0:
                                continue
                            
                            price_usd = current[0] / 100
                            
                            if price_usd < 15 or price_usd > 25:
                                continue
                            
                            profit, roi, currency = calculate_profit(price_usd, domain_id)
                            
                            if profit < 3 or roi < 20:
                                continue

                            delta = deal.get("deltaPercent", 0)
                            sales_rank = deal.get("salesRank", 0)
                            
                            if sales_rank > 150000 and sales_rank != 0:
                                continue

                            if domain_id == 1:
                                link = f"https://amazon.com/dp/{asin}"
                            else:
                                link = f"https://amazon.ca/dp/{asin}"

                            msg = (
                                f"🔥 <b>HOT FBM Deal! {country}</b>\n\n"
                                f"🛍 <b>{title}</b>\n\n"
                                f"📦 ASIN: <code>{asin}</code>\n"
                                f"🔗 {link}\n\n"
                                f"💰 Price: {currency}{price_usd:.2f}\n"
                                f"📉 Drop: {delta}%\n"
                                f"💵 FBM Profit: {currency}{profit}\n"
                                f"📈 ROI: {roi}%\n"
                                f"📊 Sales Rank: #{sales_rank:,}\n"
                            )
                            send_telegram(msg)
                            total_found += 1
                            time.sleep(2)

                        except:
                            continue
                    time.sleep(5)
                except:
                    continue

            if total_found == 0:
                send_telegram("🔍 No hot deals found this round, retrying in 1 hour...")
                
        except Exception as e:
            send_telegram(f"❌ Error: {e}")
            
        time.sleep(3600)

if __name__ == "__main__":
    main()
