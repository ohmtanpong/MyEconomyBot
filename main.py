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
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            print(f"LINE Error: {response.text}")
    except Exception as e:
        print(f"Line Connection Error: {e}")

# 3. เลือกโมเดล
def select_model():
    # ลำดับการเลือก: 1.5 Pro -> 1.5 Flash -> Pro ธรรมดา
    # *หมายเหตุ: Pro ธรรมดา ไม่รองรับ Search*
    preferred = [
        'models/gemini-1.5-pro',
        'models/gemini-1.5-pro-latest',
        'models/gemini-1.5-flash',
        'models/gemini-1.5-flash-latest',
        'models/gemini-pro'
    ]
    
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    except:
        available_models = []

    # ถ้าหาไม่เจอเลย ให้ใช้ตัว Fallback มาตรฐาน
    if not available_models:
        return 'models/gemini-pro'

    for p in preferred:
        if p in available_models:
            print(f"✅ Found Model: {p}")
            return p
    
    # ถ้าไม่เจอตัวที่ชอบเลย เอาตัวแรกที่มี
    return available_models[0]

# 4. สั่งงาน Gemini (ระบบ Hybrid: Search -> Fallback)
def get_economy_data():
    model_name = select_model()
    current_date = datetime.now().strftime("%d %B %Y")
    
    # Prompt หลัก
    base_prompt = f"""
    Current Date: {current_date}
    Role: Financial Data Analyst.
    Task: Summarize LATEST OFFICIAL economic data as of TODAY.
    Countries: 🇺🇸US, 🇨🇳China, 🇪🇺EU, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand.
    
    Required Data:
    1. GDP Growth (YoY)
    2. Inflation Rate (CPI YoY)
    3. Policy Interest Rate
    4. PMI (Manufacturing)
    5. Stock Index YTD Return (e.g. S&P500, SET)
    
    Format (Single consolidated message in THAI):
    [Flag] [Country Name in Thai]
    • GDP: [Prev]% ➡ [Actual]% (Est [Est]%)
    • CPI: [Prev]% ➡ [Actual]% (Est [Est]%)
    • Rate: [Prev]% ➡ [Actual]% (Est [Est]%)
    • PMI: [Prev] ➡ [Actual] [Emoji]
    • Stock YTD: [Index] [Return]%

    Rules:
    - Use 🟢(>50), 🔴(<50), ⚪(=50) for PMI.
    - If forecast is missing, use "-".
    - "Actual" must be the LATEST released number.
    - Add "💡 Analyst View" at the bottom.
    """

    # --- ความพยายามที่ 1: ใช้ Google Search (เฉพาะรุ่น 1.5) ---
    if "1.5" in model_name:
        try:
            print(f"🚀 Attempting Search Mode with {model_name}...")
            tools = [{"google_search": {}}]
            model = genai.GenerativeModel(model_name, tools=tools)
            
            # สั่งให้ค้นหาแบบเจาะจง
            search_prompt = base_prompt + "\nIMPORTANT: Use Google Search to verify EACH number."
            
            response = model.generate_content(
                search_prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.0) # ล็อคความนิ่ง
            )
            return response.text
        except Exception as e:
            print(f"⚠️ Search Mode Failed: {e}")
            print("🔄 Switching to Standard Mode...")

    # --- ความพยายามที่ 2: โหมดปกติ (ถ้า Search พัง หรือเป็นรุ่นเก่า) ---
    try:
        print(f"🔹 Running Standard Mode with {model_name}...")
        model = genai.GenerativeModel(model_name) # ไม่ใส่ tools
        response = model.generate_content(
            base_prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.0)
        )
        return response.text
    except Exception as e:
        return f"❌ Fatal Error: {str(e)}"

# 5. เริ่มทำงาน
if __name__ == "__main__":
    print("Process Started...")
    content = get_economy_data()
    
    header = f"📊 สรุปเศรษฐกิจโลก\n📅 ข้อมูล ณ {datetime.now().strftime('%d/%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n⚠️ AI Generated: โปรดตรวจสอบก่อนลงทุน"
    
    send_line_push(header + content + footer)
    print("Done!")
