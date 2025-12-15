import os
import requests
import json
import yfinance as yf  # พระเอกตัวจริงสำหรับหุ้น
import google.generativeai as genai
from datetime import datetime

# 1. ตั้งค่า
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LINE_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# 2. ฟังก์ชันดึงหุ้นของจริง (Real-time 100%)
def get_real_stock_data():
    print("📈 Fetching Real Stock Data from Yahoo Finance...")
    
    # รหัสหุ้นใน Yahoo Finance
    tickers = {
        "🇺🇸 S&P500": "^GSPC",
        "🇨🇳 Shanghai": "000001.SS",
        "🇪🇺 Stoxx50": "^STOXX50E",
        "🇯🇵 Nikkei": "^N225",
        "🇮🇳 Nifty": "^NSEI",
        "🇰🇷 KOSPI": "^KS11",
        "🇻🇳 VN-Index": "^VNINDEX", # บางที Yahoo อาจดึงเวียดนามช้า ถ้า Error จะข้าม
        "🇹🇭 SET": "^SET.BK"
    }
    
    stock_report = ""
    current_year = datetime.now().year
    
    for country, symbol in tickers.items():
        try:
            stock = yf.Ticker(symbol)
            # ดึงประวัติราคาตั้งแต่ต้นปี
            hist = stock.history(start=f"{current_year}-01-01")
            
            if not hist.empty:
                start_price = hist.iloc[0]['Close']
                current_price = hist.iloc[-1]['Close']
                change_pct = ((current_price - start_price) / start_price) * 100
                
                # ใส่เครื่องหมาย + หรือ -
                sign = "+" if change_pct >= 0 else ""
                stock_report += f"{country}: {sign}{change_pct:.2f}% (Price: {current_price:,.0f})\n"
            else:
                stock_report += f"{country}: N/A (Data Error)\n"
        except Exception as e:
            stock_report += f"{country}: N/A\n"
            
    return stock_report

# 3. ฟังก์ชัน AI (หาแค่ GDP/CPI/Rates)
def get_economy_with_ai(stock_text):
    print("🤖 AI searching for Macro Data...")
    
    # พยายามใช้ 1.5 Flash (เร็วและรองรับ Search)
    model = genai.GenerativeModel('models/gemini-1.5-flash') 
    
    current_date = datetime.now().strftime("%d %B %Y")
    
    prompt = f"""
    Current Date: {current_date}
    
    I have already fetched the Real-Time Stock Market Data:
    {stock_text}
    
    YOUR TASK:
    Use Google Search to find the LATEST OFFICIAL Macro Economic Data for:
    🇺🇸US, 🇨🇳China, 🇪🇺Eurozone, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand.
    
    Find specific latest numbers for:
    1. GDP Growth Rate (YoY) - Latest announced quarter
    2. Inflation Rate (CPI YoY) - Latest announced month
    3. Central Bank Interest Rate - Current level
    4. Manufacturing PMI - Latest month
    
    OUTPUT FORMAT (Combine my Stock Data with your found Macro Data):
    Create a consolidated summary in THAI Language.
    
    [Flag] [Country Name]
    • GDP: [Actual]% (Ref: [Month/Quarter])
    • CPI: [Actual]%
    • Rate: [Actual]%
    • PMI: [Actual] [Emoji]
    • YTD Stock: [Insert valid data from my list above]
    
    Rules:
    - PMI Emoji: 🟢(>50), 🔴(<50)
    - **ACCURACY IS CRITICAL**. If you cannot find the official number via search, write "-". DO NOT GUESS.
    - Do not invent stock numbers, use ONLY what I provided.
    - Add "💡 Analyst View" at the bottom (2 sentences).
    """
    
    # เปิดโหมด Search
    tools = [{"google_search": {}}]
    try:
        response = model.generate_content(prompt, tools=tools)
        return response.text
    except Exception as e:
        # ถ้า Search พัง ให้ตอบ Error ดีกว่าตอบมั่ว
        return f"❌ เกิดข้อผิดพลาดในการค้นหาข้อมูล: {str(e)}"

# 4. ส่งไลน์
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

# 5. เริ่มทำงาน
if __name__ == "__main__":
    # 1. ดึงหุ้นจริงก่อน
    real_stock_data = get_real_stock_data()
    
    # 2. เอาหุ้นไปให้ AI เขียนข่าวเศรษฐกิจประกอบ
    final_content = get_economy_with_ai(real_stock_data)
    
    # 3. ส่งผลลัพธ์
    header = f"📊 สรุปเศรษฐกิจ & หุ้นโลก (Hybrid Real-Time)\n📅 ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n✅ หุ้น: Real-time Data (Yahoo Finance)\n🤖 ศก.: AI Google Search"
    
    send_line_push(header + final_content + footer)
    print("Done!")
