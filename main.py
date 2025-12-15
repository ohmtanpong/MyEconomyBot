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

def get_economy_summary():
    current_date = datetime.now().strftime("%B %Y")
    
    # --- ส่วนสำคัญ: ระบบค้นหาโมเดลอัตโนมัติ (Auto-Detect) ---
    print("🔍 กำลังค้นหาโมเดลที่ใช้งานได้...")
    valid_model = None
    
    try:
        # สั่งให้ Google List รายชื่อโมเดลทั้งหมดออกมา
        for m in genai.list_models():
            # หาโมเดลที่สามารถ Generate Content ได้ (ตัดพวกโมเดลฝังตัวออก)
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ เจอโมเดล: {m.name}")
                # เลือกตัวที่เป็นรุ่น 1.5 หรือ Pro หรือ Flash ก่อน
                if 'flash' in m.name or 'pro' in m.name:
                    valid_model = m.name
                    break # เจอแล้วหยุดหาเลย เอาตัวนี้แหละ
        
        # ถ้าหา Flash/Pro ไม่เจอเลย ให้เอาตัวแรกสุดที่เจอ
        if not valid_model:
             for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    valid_model = m.name
                    break
                    
    except Exception as e:
        return f"❌ API Key มีปัญหาครับ: {str(e)}\n(ลองเช็คใน GitHub Secrets ว่ามีช่องว่างติดมาไหม)"

    if not valid_model:
        return "❌ เชื่อมต่อได้ แต่ไม่พบโมเดลที่ใช้งานได้เลย (แปลกมาก)"

    print(f"🚀 ตกลงใช้โมเดล: {valid_model}")
    
    # --- เริ่มสร้างเนื้อหา ---
    model = genai.GenerativeModel(valid_model)
    
    prompt = f"""
    สรุปเศรษฐกิจโลกเดือน {current_date}
    ประเทศ: 🇺🇸US, 🇨🇳China, 🇪🇺EU, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand
    
    ข้อมูล 6 ตัวชี้วัด (ล่าสุด):
    1. GDP Growth
    2. Inflation Rate
    3. Unemployment
    4. Interest Rate
    5. PMI
    6. **Stock Market YTD Return** (ระบุชื่อดัชนี)
    
    รูปแบบ: ภาษาไทย สั้นกระชับ แยกรายประเทศ (Emoji ธงชาติ)
    ปิดท้ายด้วย "💡 มุมมองการลงทุน"
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ โมเดล {valid_model} Error: {str(e)}"

# เริ่มทำงาน
if __name__ == "__main__":
    print("Starting...")
    summary = get_economy_summary()
    
    header = f"📊 สรุปเศรษฐกิจ (Auto-Detect)\n📅 {datetime.now().strftime('%m/%Y')}\n{'-'*15}\n"
    send_line_push(header + summary)
    print("Done!")
