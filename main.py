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

# 2. ฟังก์ชันส่งไลน์ (ส่งทีเดียว ข้อความเดียว)
def send_line_push(message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    data = {
        'to': LINE_USER_ID,
        'messages': [{'type': 'text', 'text': message}] # ส่งเป็นก้อนเดียว
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(f"LINE Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending LINE: {e}")

# 3. ระบบค้นหาโมเดลอัตโนมัติ (แก้ปัญหา 404)
def select_best_model():
    print("🔍 Auto-detecting available models...")
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            return None, "No models found."

        # ลำดับความสำคัญ: Flash -> Pro -> อะไรก็ได้
        preferred = [
            'models/gemini-1.5-flash',
            'models/gemini-1.5-flash-latest',
            'models/gemini-1.5-pro',
            'models/gemini-pro'
        ]
        
        # เลือกตัวที่ดีที่สุดที่มีในบัญชี
        for p in preferred:
            if p in available_models:
                print(f"✅ Selected: {p}")
                return p, None
        
        # ถ้าไม่เจอตัวที่ชอบ เอาตัวแรกที่มีเลย
        print(f"✅ Selected (Fallback): {available_models[0]}")
        return available_models[0], None

    except Exception as e:
        return None, str(e)

# 4. สั่งงาน Gemini
def get_economy_data():
    model_name, error = select_best_model()
    if error:
        return f"❌ System Error: {error}"

    model = genai.GenerativeModel(model_name)
    current_date = datetime.now().strftime("%B %Y")
    
    prompt = f"""
    Task: Summarize LATEST OFFICIAL economic data for {current_date}.
    Countries: 🇺🇸US, 🇨🇳China, 🇪🇺EU, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand.
    
    Output Format:
    Create a single consolidated list in THAI language.
    For each country, show these 5 lines (Compact style):
    [Flag] [Country Name]
    • GDP: [Prev]% ➡ [Actual]% (Est [Fcst]%)
    • CPI: [Prev]% ➡ [Actual]% (Est [Fcst]%)
    • Rate: [Prev]% ➡ [Actual]% (Est [Fcst]%)
    • PMI: [Prev] ➡ [Actual] [Status_Emoji]
    • Stock YTD: [Index] [Return]%
    
    Status Emoji for PMI: 🟢(>50), 🔴(<50), ⚪(=50)
    
    Rules:
    1. Compare 3 points: Previous -> Actual (Forecast). If Forecast is missing, use "-".
    2. Use OFFICIAL data only.
    3. Keep it strictly compact.
    4. Analyst View: At the bottom, add 2 sentences on the best market to invest in.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Generate Error: {str(e)}"

# 5. เริ่มทำงาน
if __name__ == "__main__":
    print("Generating content...")
    content = get_economy_data()
    
    # รวมทุกส่วนเป็น String เดียว (ข้อความเดียว)
    header = f"📊 สรุปเศรษฐกิจโลก (3-Point Data)\n📅 ประจำเดือน {datetime.now().strftime('%m/%Y')}\n{'-'*20}\n"
    footer = f"\n{'-'*20}\n⚠️ AI Generated: โปรดตรวจสอบก่อนลงทุน"
    
    full_message = header + content + footer
    
    print("Sending single message to LINE...")
    send_line_push(full_message)
    print("Done!")
