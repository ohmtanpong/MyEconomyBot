import os
import requests
import json
import google.generativeai as genai
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

# 3. ค้นหาโมเดล
def select_best_model():
    print("🔍 Auto-detecting models...")
    try:
        available = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available.append(m.name)
        
        if not available: return None, "No models found."

        # ลำดับการเลือก: Flash -> Pro
        preferred = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        for p in preferred:
            if p in available:
                print(f"✅ Selected Model: {p}") # บรรทัดนี้จะบอกชื่อโมเดลใน Log
                return p, None
        
        return available[0], None

    except Exception as e:
        return None, str(e)

# 4. สั่งงาน Gemini (แก้ Prompt ใหม่)
def get_economy_data():
    model_name, error = select_best_model()
    if error: return f"System Error: {error}"

    model = genai.GenerativeModel(model_name)
    current_date = datetime.now().strftime("%d %B %Y")
    
    # --- PROMPT แก้ไขใหม่ ---
    prompt = f"""
    Role: Senior Economist.
    Current Date: {current_date}
    
    Task: Retrieve the MOST RECENTLY RELEASED official economic indicators available as of TODAY.
    Countries: 🇺🇸US, 🇨🇳China, 🇪🇺Eurozone, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand.
    
    Format Definitions:
    - [Prev]: The data from the period BEFORE the latest release.
    - [Actual]: The LATEST OFFICIAL RELEASED number (e.g., if today is Dec, CPI might be Nov data).
    - [Est]: The Consensus Forecast for the next release (if available, else "-").
    
    Required Output Format (Single consolidated message in THAI):
    [Flag] [Country Name in Thai]
    • GDP: [Prev]% ➡ [Actual]% (Est [Est]%)
    • CPI: [Prev]% ➡ [Actual]% (Est [Est]%)
    • Rate: [Prev]% ➡ [Actual]% (Est [Est]%)
    • PMI: [Prev] ➡ [Actual] [Emoji]
    • Stock YTD: [Index Name] [Return]%
    
    PMI Emoji: 🟢(>50), 🔴(<50), ⚪(=50)
    
    Strict Rules:
    1. Do NOT say "data not available for current month". Always provide the LATEST AVAILABLE data from previous months/quarters.
    2. Only use OFFICIAL numbers.
    3. Add "💡 Analyst View" at the bottom (2 sentences summary).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Generate Error: {str(e)}"

# 5. เริ่มทำงาน
if __name__ == "__main__":
    print("Process Started...")
    content = get_economy_data()
    
    header = f"📊 สรุปเศรษฐกิจโลก (ล่าสุด)\n📅 ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n⚠️ AI Generated: เช็คข้อมูลทางการอีกครั้ง"
    
    send_line_push(header + content + footer)
    print("Done!")
