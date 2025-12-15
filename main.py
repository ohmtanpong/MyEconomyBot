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
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 200:
            print(f"LINE Error: {response.status_code} {response.text}")
        else:
            print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending LINE: {e}")

# 3. สั่งงาน Gemini
def get_economy_summary():
    # --- ใช้รุ่นมาตรฐาน gemini-pro (เสถียรที่สุด) ---
    print("Using model: gemini-pro")
    model = genai.GenerativeModel('gemini-pro')
    
    current_date = datetime.now().strftime("%B %Y")
    
    prompt = f"""
    คุณคือนักกลยุทธ์การลงทุนและเศรษฐศาสตร์อาวุโส 
    ช่วยสรุป "ข้อมูลเศรษฐกิจและตลาดหุ้นล่าสุด" ของเดือน {current_date}
    
    สำหรับกลุ่มประเทศ/เขตเศรษฐกิจ:
    1. 🇺🇸 สหรัฐฯ (US)
    2. 🇨🇳 จีน (China)
    3. 🇪🇺 ยูโรโซน (EU) - *เพิ่มตามคำขอ*
    4. 🇯🇵 ญี่ปุ่น (Japan)
    5. 🇮🇳 อินเดีย (India)
    6. 🇰🇷 เกาหลีใต้ (South Korea)
    7. 🇻🇳 เวียดนาม (Vietnam)
    8. 🇹🇭 ไทย (Thailand)
    
    ขอข้อมูล 6 ตัวชี้วัด (เน้นตัวเลขล่าสุดที่ประกาศออกมา):
    1. GDP Growth (% YoY)
    2. Inflation Rate (เงินเฟ้อ % YoY)
    3. Unemployment Rate (อัตราว่างงาน %)
    4. Interest Rate (ดอกเบี้ยนโยบาย %)
    5. PMI (Manufacturing)
    6. **Stock Market YTD Return** (ผลตอบแทนดัชนีหุ้นหลักตั้งแต่ต้นปี % เช่น S&P500, STOXX600, SET, VN30)
    
    รูปแบบการตอบ:
    - เขียนสรุปเป็นภาษาไทย อ่านง่าย สั้นกระชับ (Style: Morning Brief)
    - **ไม่ต้องทำตาราง** ให้แยกเป็นหัวข้อรายประเทศ (ใส่ Emoji ธงชาติหน้าชื่อประเทศ)
    - ปิดท้ายด้วย "💡 มุมมองการลงทุนเดือนนี้": เลือก 1-2 ประเทศที่น่าสนใจที่สุด
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"เกิดข้อผิดพลาดจาก Gemini (gemini-pro): {str(e)}"

# 4. เริ่มทำงาน
if __name__ == "__main__":
    print("Getting data from Gemini...")
    summary = get_economy_summary()
    
    print("Sending to LINE...")
    header_msg = f"📊 สรุปเศรษฐกิจ & หุ้นทั่วโลก (EU+YTD)\n📅 ประจำเดือน {datetime.now().strftime('%m/%Y')}\n{'-'*20}\n"
    
    # รวมหัวข้อกับเนื้อหา
    full_msg = header_msg + summary
    
    send_line_push(full_msg)
    print("Done!")
