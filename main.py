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
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            print(f"LINE Error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error sending LINE: {e}")

# 3. สั่งงาน Gemini
def get_economy_summary():
    # ระบบ Auto-Detect เลือกโมเดลที่ฉลาดที่สุดก่อน
    valid_model = None
    try:
        # ลองหา Pro หรือ Flash 1.5 ก่อน
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-pro' in m.name:
                    valid_model = m.name; break
        # ถ้าไม่มี เอา Flash
        if not valid_model:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    if 'gemini-1.5-flash' in m.name:
                        valid_model = m.name; break
        # ถ้าไม่มีจริงๆ เอาอะไรก็ได้
        if not valid_model:
            valid_model = 'gemini-pro'
    except:
        valid_model = 'gemini-pro'

    print(f"Using Model: {valid_model}")
    model = genai.GenerativeModel(valid_model)
    
    current_date = datetime.now().strftime("%B %Y")
    
    # --- Prompt ที่ปรับปรุงใหม่ (Strict Data & Formatting) ---
    prompt = f"""
    Act as a professional economist. Summarize the LATEST OFFICIAL economic indicators for:
    🇺🇸USA, 🇨🇳China, 🇪🇺Eurozone, 🇯🇵Japan, 🇮🇳India, 🇰🇷South Korea, 🇻🇳Vietnam, 🇹🇭Thailand.
    
    Current Date: {current_date}
    
    Please present the data in this EXACT format for each country:
    
    [Flag Emoji] [Country Name]
    • GDP: [Prev]% ➡ [Current]% (Est [Forecast]%)
    • CPI: [Prev]% ➡ [Current]% (Est [Forecast]%)
    • Rate: [Prev]% ➡ [Current]% (Est [Forecast]%)
    • PMI: [Prev] ➡ [Current] ([Status Emoji])
    • YTD Stock: [Index Name] [+/-Return]%
    
    Indicators Key:
    - GDP: GDP Growth Rate (YoY)
    - CPI: Inflation Rate (YoY)
    - Rate: Central Bank Interest Rate
    - PMI: Manufacturing PMI (Use 🟢 for >50, 🔴 for <50, ⚪ for 50)
    - YTD Stock: Year-to-Date return of the main index.
    
    Rules:
    1. Only use OFFICIAL announced numbers. If "Forecast" is unavailable, use "-".
    2. Comparison: Show Previous vs Current to see the trend.
    3. Keep it clean and readable for a chat app (LINE).
    4. **Translate everything into THAI Language.**
    5. Add a "💡 Analyst View" at the very end (1-2 sentences on who looks strongest).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาดในการดึงข้อมูล: {str(e)}"

# 4. เริ่มทำงาน
if __name__ == "__main__":
    print("Generating...")
    summary = get_economy_summary()
    
    # ส่วนหัวข้อความ
    header = f"📊 สรุปตัวเลขเศรษฐกิจ (3-Point Data)\n📅 ข้อมูลล่าสุด ณ {datetime.now().strftime('%m/%Y')}\n{'-'*25}\n"
    
    # ส่วน Disclaimer (สำคัญมาก เพื่อเตือนเรื่องความแม่นยำ)
    footer = f"\n{'-'*25}\n⚠️ หมายเหตุ: ข้อมูลสังเคราะห์โดย AI โปรดตรวจสอบแหล่งข้อมูลทางการ (Investing/Bloomberg) อีกครั้งก่อนตัดสินใจลงทุน"
    
    # ส่งเข้า LINE
    send_line_push(header + summary + footer)
    print("Done!")
