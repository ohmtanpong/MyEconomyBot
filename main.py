import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

# 1. ตั้งค่า API และตัวแปร
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LINE_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# 2. ฟังก์ชันส่งไลน์ (Push Message)
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
        else:
            print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending LINE: {e}")

# 3. สั่งงาน Gemini แบบมีระบบกันพลาด (Smart Fallback)
def get_economy_summary():
    current_date = datetime.now().strftime("%B %Y")
    
    # รายชื่อโมเดลที่จะให้ลองใช้ (เรียงจากใหม่ไปเก่า)
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-001',
        'gemini-1.5-pro',
        'gemini-1.5-pro-001',
        'gemini-pro'
    ]
    
    prompt = f"""
    สรุป "ข้อมูลเศรษฐกิจและตลาดหุ้นล่าสุด" เดือน {current_date}
    กลุ่มประเทศ: 🇺🇸US, 🇨🇳China, 🇪🇺EU, 🇯🇵Japan, 🇮🇳India, 🇰🇷Korea, 🇻🇳Vietnam, 🇹🇭Thailand
    
    ขอข้อมูล 6 ตัวชี้วัด (เน้นตัวเลขล่าสุด):
    1. GDP Growth (% YoY)
    2. Inflation Rate (% YoY)
    3. Unemployment Rate (%)
    4. Interest Rate (%)
    5. PMI (Manufacturing)
    6. **Stock Market YTD Return** (ระบุชื่อดัชนี เช่น S&P500, SET, STOXX600)
    
    รูปแบบ: สรุปภาษาไทย สั้นกระชับ แยกรายประเทศ (Emoji ธงชาติ) 
    ปิดท้ายด้วย "💡 มุมมองการลงทุนเดือนนี้"
    """

    # วนลูปหาโมเดลที่ใช้ได้
    for model_name in models_to_try:
        print(f"Testing model: {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            print(f"Success with {model_name}!")
            return response.text # ถ้าสำเร็จ ให้ส่งคำตอบกลับไปเลย
        except Exception as e:
            print(f"Failed {model_name}: {str(e)}")
            continue # ถ้าพัง ให้ไปลองตัวถัดไป
            
    return "ขออภัยครับ ไม่สามารถเชื่อมต่อกับโมเดลใดๆ ได้เลย (All models failed)."

# 4. เริ่มทำงาน
if __name__ == "__main__":
    print("Starting process...")
    summary = get_economy_summary()
    
    print("Sending to LINE...")
    header_msg = f"📊 สรุปเศรษฐกิจ & หุ้นโลก (EU+YTD)\n📅 ประจำเดือน {datetime.now().strftime('%m/%Y')}\n{'-'*20}\n"
    
    send_line_push(header_msg + summary)
    print("Process Finished!")
