import os
import requests
import json
import yfinance as yf
from duckduckgo_search import DDGS
import google.generativeai as genai
from datetime import datetime
import time

# 1. ตั้งค่า
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LINE_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# 2. ฟังก์ชันดึงหุ้น (Yahoo Finance)
def get_stock_data():
    print("📈 Fetching Stocks...")
    tickers = {
        "🇺🇸 S&P500": "^GSPC",
        "🇨🇳 Shanghai": "000001.SS",
        "🇪🇺 Stoxx50": "^STOXX50E",
        "🇯🇵 Nikkei": "^N225",
        "🇮🇳 Nifty": "^NSEI",
        "🇰🇷 KOSPI": "^KS11",
        "🇻🇳 VN-Index": "^VNINDEX",
        "🇹🇭 SET": "^SET.BK"
    }
    
    report = "📊 REAL-TIME STOCK DATA:\n"
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # พยายามดึงข้อมูลล่าสุด
            hist = ticker.history(period="5d") # เอา 5 วันย้อนหลังเผื่อติดวันหยุด
            if not hist.empty:
                last_price = hist['Close'].iloc[-1]
                
                # หา % YTD แบบคร่าวๆ (เทียบกับวันแรกของปีในข้อมูล 5 วันอาจไม่ได้ ต้องเทียบกับ prev close)
                # เพื่อความแม่นยำเรื่อง YTD เราจะดึงข้อมูล ytd จริงๆ
                ytd_hist = ticker.history(period="ytd")
                if not ytd_hist.empty:
                    start_price = ytd_hist['Close'].iloc[0]
                    change = ((last_price - start_price) / start_price) * 100
                    sign = "+" if change >= 0 else ""
                    report += f"{name}: {sign}{change:.2f}% (Price: {last_price:,.0f})\n"
                else:
                    report += f"{name}: N/A\n"
            else:
                report += f"{name}: N/A\n"
        except:
            report += f"{name}: N/A\n"
    return report

# 3. ฟังก์ชันค้นหาข่าวเศรษฐกิจ (DuckDuckGo)
def search_economy_data():
    print("🌍 Searching Economy News...")
    countries = [
        "United States", "China", "Eurozone", "Japan", 
        "India", "South Korea", "Vietnam", "Thailand"
    ]
    
    search_results = "📰 LATEST ECONOMIC NEWS SNIPPETS:\n"
    ddgs = DDGS()
    
    for country in countries:
        try:
            # ค้นหาคำว่า "Latest GDP Inflation Interest Rate [Country] 2025"
            query = f"latest GDP inflation interest rate {country} official data released 2024 2025 tradingeconomics"
            results = ddgs.text(query, max_results=2) # เอา 2 ผลลัพธ์แรก
            
            search_results += f"\n--- {country} ---\n"
            if results:
                for r in results:
                    search_results += f"- {r['body']}\n"
            else:
                search_results += "No data found via Search.\n"
            
            time.sleep(1) # พักนิดนึงป้องกันโดนบล็อก
        except Exception as e:
            search_results += f"{country}: Search Error ({str(e)})\n"
            
    return search_results

# 4. ฟังก์ชัน AI (สรุปข้อมูล)
def generate_summary(stock_text, news_text):
    print("🤖 AI Summarizing...")
    # ใช้รุ่น Flash ธรรมดา ไม่ต้องใช้ Tools แล้ว เพราะเราป้อนข้อมูลให้มันเอง
    model = genai.GenerativeModel('models/gemini-1.5-flash')
    
    current_date = datetime.now().strftime("%d %B %Y")
    
    prompt = f"""
    Current Date: {current_date}
    
    INPUT DATA 1 (Stocks - Real):
    {stock_text}
    
    INPUT DATA 2 (Economy - Search Results):
    {news_text}
    
    TASK:
    Act as a professional economist. Use the PROVIDED INPUT DATA to create a summary.
    Do not invent numbers. If the search results don't have the specific number, write "-".
    
    OUTPUT FORMAT (THAI Language):
    [Flag] [Country Name]
    • GDP: [Prev]% ➡ [Actual]%
    • CPI: [Prev]% ➡ [Actual]%
    • Rate: [Actual]%
    • PMI: [Actual] [Emoji]
    • YTD Stock: [Return from Input 1]%
    
    Rules:
    - PMI Emoji: 🟢(>50), 🔴(<50)
    - "Actual" must be from the Search Results provided.
    - Rate = Central Bank Policy Rate.
    - Analyst View: 2 sentences at the bottom.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# 5. ส่งไลน์
def send_line_push(message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    data = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': message}]
    }
    requests.post(url, headers=headers, data=json.dumps(data))

# เริ่มทำงาน
if __name__ == "__main__":
    # 1. หาหุ้น
    stocks = get_stock_data()
    
    # 2. หาข่าวเศรษฐกิจ
    news = search_economy_data()
    
    # 3. ให้ AI สรุป
    final_content = generate_summary(stocks, news)
    
    # 4. ส่งผลลัพธ์
    header = f"📊 สรุปเศรษฐกิจโลก (DDG Search)\n📅 ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n✅ Data Source: Yahoo Finance & DuckDuckGo"
    
    send_line_push(header + final_content + footer)
    print("Done!")
