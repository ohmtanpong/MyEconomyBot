import os
import requests
import json
import google.generativeai as genai
from datetime import datetime

# 1. ตั้งค่า API และตัวแปรจาก GitHub Secrets
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
LINE_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

genai.configure(api_key=GEMINI_API_KEY)

# 2. ฟังก์ชันส่งไลน์ผ่าน Messaging API (Push Message)
def send_line_push(message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    data = {
        'to': LINE_USER_ID,
        'messages': [
            {
                'type': 'text',
                'text': message
            }
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f"LINE Response: {response.status_code} {response.text}")

# 3. สั่งงาน Gemini
def get_economy_summary():
    model = genai.GenerativeModel('gemini-1.5-flash')
    current_date = datetime.now().strftime("%B %Y")
    
    prompt = f"""
    คุณคือนักเศรษฐศาสตร์ ช่วยสรุปตัวเลขเศรษฐกิจล่าสุด ณ เดือน {current_date} 
    ของประเทศ: จีน, อินเดีย, ไทย, เวียดนาม, สหรัฐฯ, เกาหลีใต้, ญี่ปุ่น
    
    ขอข้อมูล 5 ตัวชี้วัด:
    1. GDP Growth
    2. Inflation Rate
    3. Unemployment Rate
    4. Interest Rate
    5. PMI
    
    รูปแบบการตอบ:
    - สรุปสั้นๆ เป็นภาษาไทย
    - ใช้ Emoji ตกแต่งให้อ่านง่าย
    - เน้นตัวเลขล่าสุด
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาด: {str(e)}"

# 4. เริ่มทำงาน
if __name__ == "__main__":
    print("Getting data from Gemini...")
    summary = get_economy_summary()
    print("Sending to LINE...")
    send_line_push(f"📊 สรุปเศรษฐกิจประจำเดือน\n{summary}")
    print("Done!")
