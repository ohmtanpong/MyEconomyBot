import os
import requests
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime

# 1. ตั้งค่า
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LINE_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# 2. ฟังก์ชันส่งไลน์
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
    try:
        requests.post(url, headers=headers, data=json.dumps(data))
    except Exception as e:
        print(f"Line Error: {e}")

# 3. เลือกโมเดล
def select_best_model():
    print("🔍 Auto-detecting models...")
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        
        if not available: return None, "No models found."
        
        # เน้นโมเดลที่รองรับ Search Tool ได้ดี
        preferred = [
            'models/gemini-1.5-pro', # ตัวนี้เก่งสุดเรื่องค้นหา
            'models/gemini-1.5-pro-latest',
            'models/gemini-1.5-flash',
            'models/gemini-pro'
        ]
        
        for p in preferred:
            if p in available:
                print(f"✅ Selected Model: {p}")
                return p, None
        
        return available[0], None

    except Exception as e:
        return None, str(e)

# 4. สั่งงาน Gemini (โหมดแม่นยำพิเศษ)
def get_economy_data():
    model_name, error = select_best_model()
    if error: return f"System Error: {error}"

    # --- ส่วนสำคัญ 1: เปิดใช้ Google Search Tool ---
    # ทำให้โมเดลค้นหาข้อมูลล่าสุดจาก Google ได้จริง
    tools = [
        {"google_search": {}} 
    ]
    
    # สร้างโมเดลพร้อมเครื่องมือ
    model = genai.GenerativeModel(model_name, tools=tools)
    
    current_date = datetime.now().strftime("%d %B %Y")
    
    # --- ส่วนสำคัญ 2: ล็อคความนิ่ง (Temperature = 0) ---
    generation_config = genai.types.GenerationConfig(
        temperature=0.0  # 0.0 = แม่นยำที่สุด ห้ามสุ่ม ห้ามมั่ว
    )

    prompt = f"""
    Current Date: {current_date}
    Role: Financial Data Analyst.
    
    Task: Use Google Search to find the LATEST OFFICIAL RELEASED economic data as of TODAY.
    Countries: 🇺🇸US, 🇨🇳China, 🇪🇺Eurozone, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand.
    
    Data Points Required:
    1. GDP Growth (YoY)
    2. Inflation Rate (CPI YoY)
    3. Central Bank Interest Rate
    4. Manufacturing PMI
    5. Main Stock Index YTD Return (e.g., S&P500, SET, VN30, NIKKEI)
    
    Format Definitions:
    - [Prev]: The data from the period immediately BEFORE the latest release.
    - [Actual]: The MOST RECENTLY RELEASED official number.
    - [Est]: The Consensus Forecast for the NEXT release (if found, else "-").
    
    Output Format (Single consolidated message in THAI Language):
    [Flag] [Country Name in Thai]
    • GDP: [Prev]% ➡ [Actual]% (Est [Est]%)
    • CPI: [Prev]% ➡ [Actual]% (Est [Est]%)
    • Rate: [Prev]% ➡ [Actual]% (Est [Est]%)
    • PMI: [Prev] ➡ [Actual] [Emoji]
    • Stock YTD: [Index Name] [Return]%
    
    PMI Emoji: 🟢(>50), 🔴(<50), ⚪(=50)
    
    Strict Rules:
    1. ACCURACY IS PARAMOUNT. Use search results. Do not hallucinate.
    2. If "Forecast/Est" is not found in search results, stick to "-" (Dash).
    3. "Actual" must be the latest announced figure (e.g., if today is Dec 15, CPI might be from Nov).
    4. Provide a brief "💡 Analyst View" at the end.
    """
    
    try:
        # ส่งคำสั่งพร้อม Config
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
    except Exception as e:
        return f"Generate Error: {str(e)}"

# 5. เริ่มทำงาน
if __name__ == "__main__":
    print("Process Started...")
    content = get_economy_data()
    
    header = f"📊 สรุปเศรษฐกิจโลก (Search Mode)\n📅 ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n⚠️ ข้อมูลจากการค้นหา Google Search โดย AI"
    
    send_line_push(header + content + footer)
    print("Done!")
