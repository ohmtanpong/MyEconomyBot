import os
import requests
import json
import time
import yfinance as yf
from duckduckgo_search import DDGS
import google.generativeai as genai
from datetime import datetime

# 1. ตั้งค่า
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LINE_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# 2. ฟังก์ชันเลือกโมเดล (นำระบบสแกนกลับมาใช้)
def select_best_model():
    print("🔍 Scanning available models...")
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return None, "No models found."

        # ลำดับความสำคัญ: Flash -> Pro -> อะไรก็ได้ที่มี
        preferred_order = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-flash-001',
            'models/gemini-1.5-pro',
            'models/gemini-1.5-pro-latest',
            'models/gemini-pro'
        ]
        
        for p in preferred_order:
            if p in available_models:
                print(f"✅ Selected Model: {p}")
                return p, None
        
        # ถ้าไม่เจอตัวที่ชอบ เอาตัวแรกที่มีเลย
        fallback = available_models[0]
        print(f"✅ Selected Fallback: {fallback}")
        return fallback, None

    except Exception as e:
        return None, str(e)

# 3. ฟังก์ชันดึงหุ้น (Yahoo Finance)
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
    
    report = "📊 REAL-TIME STOCK DATA (YTD):\n"
    current_year = datetime.now().year
    
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # ดึงข้อมูลตั้งแต่ต้นปี
            hist = ticker.history(start=f"{current_year}-01-01")
            
            if not hist.empty:
                start_price = hist.iloc[0]['Close']
                current_price = hist.iloc[-1]['Close']
                change_pct = ((current_price - start_price) / start_price) * 100
                
                sign = "+" if change_pct >= 0 else ""
                report += f"{name}: {sign}{change_pct:.2f}%\n"
            else:
                report += f"{name}: N/A\n"
        except:
            report += f"{name}: N/A\n"
    return report

# 4. ฟังก์ชันค้นหาข่าวเศรษฐกิจ (DuckDuckGo)
def search_economy_data():
    print("🌍 Searching Economy News via DuckDuckGo...")
    countries = [
        "United States", "China", "Eurozone", "Japan", 
        "India", "South Korea", "Vietnam", "Thailand"
    ]
    
    search_results = "📰 LATEST ECONOMIC NEWS SNIPPETS:\n"
    ddgs = DDGS()
    
    for country in countries:
        try:
            # ค้นหาคำว่า "Latest GDP Inflation Interest Rate [Country] released 2024 2025"
            query = f"latest GDP growth inflation rate interest rate {country} official data released 2024 2025 tradingeconomics"
            results = ddgs.text(query, max_results=2)
            
            search_results += f"\n--- {country} ---\n"
            if results:
                for r in results:
                    search_results += f"- {r['body']}\n"
            else:
                search_results += "No data found.\n"
            
            time.sleep(1) # พักนิดนึง
        except Exception as e:
            search_results += f"{country}: Search Error\n"
            
    return search_results

# 5. ฟังก์ชัน AI (สรุปข้อมูล)
def generate_summary(stock_text, news_text):
    # เลือกโมเดลก่อน (แก้ 404)
    model_name, error = select_best_model()
    if error: return f"System Error: {error}"

    print(f"🤖 AI Summarizing using {model_name}...")
    model = genai.GenerativeModel(model_name)
    
    current_date = datetime.now().strftime("%d %B %Y")
    
    prompt = f"""
    Current Date: {current_date}
    
    INPUT DATA 1 (Stocks - Real YTD):
    {stock_text}
    
    INPUT DATA 2 (Economy - Search Snippets):
    {news_text}
    
    TASK:
    Act as a professional economist. Summarize the OFFICIAL data from the Inputs.
    
    OUTPUT FORMAT (THAI Language):
    [Flag] [Country Name in Thai]
    • GDP: [Prev]% ➡ [Actual]%
    • CPI: [Prev]% ➡ [Actual]%
    • Rate: [Actual]%
    • PMI: [Actual] [Emoji]
    • YTD Stock: [Return from Input 1]%
    
    Rules:
    - Extract "Actual" numbers from the Search Snippets.
    - If "Prev" (Previous) is found in snippet, show it. If not, just show Actual.
    - If specific data is missing in snippet, use "-". DO NOT GUESS.
    - Rate = Central Bank Policy Rate.
    - PMI Emoji: 🟢(>50), 🔴(<50), ⚪(=50)
    - Analyst View: 2 sentences at the bottom (Based on the data).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# 6. ส่งไลน์
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
    header = f"📊 สรุปเศรษฐกิจโลก (Real-Time)\n📅 ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n✅ Data Source: Yahoo Finance & DuckDuckGo"
    
    send_line_push(header + final_content + footer)
    print("Done!")
