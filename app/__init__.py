import fasttext
from pythainlp.util import Trie
import re
from pythainlp.tokenize import word_tokenize
from datetime import datetime, timedelta
import time
import json

MODEL_PATH = "file/kl90.model"  # เปลี่ยนเป็นพาธที่ถูกต้อง
model = fasttext.load_model(MODEL_PATH)

with open("file/day_mapping.json", "r", encoding="utf-8") as file:
    day_mapping = json.load(file)
with open("file/month_mapping.json", "r", encoding="utf-8") as file:
    month_mapping = json.load(file)
with open("file/hour_mapping.json", "r", encoding="utf-8") as file:
    hour_mapping = json.load(file)
with open("file/minute_mapping.json", "r", encoding="utf-8") as file:
    minute_mapping = json.load(file)
with open("file/month_dict.json", "r", encoding="utf-8") as file:
    month_dict = json.load(file)
with open("file/month_key.json", "r", encoding="utf-8") as file:
    month_key = json.load(file)
with open("file/label.json", "r", encoding="utf-8") as file:
    label_mapping = json.load(file)
with open("file/words.json", "r", encoding="utf-8") as file:
    words_mapping = json.load(file)




def predict_text(text: str):
    tokenized_text = ' '.join(word_tokenize(text, engine='newmm'))
    labels, confidence  = model.predict(tokenized_text)
    cleaned_label = labels[0].replace('__label__', '')

    return cleaned_label

def modified_token(text: str):
    # tokenized_text = ' '.join(word_tokenize(text, engine='newmm'))
    custom_words_path = "file/word.txt"
    with open(custom_words_path, "r", encoding="utf-8") as file:
        custom_words = [line.strip() for line in file]
    trie = Trie(custom_words)
    tokenized_text_new = word_tokenize(text, custom_dict=trie)
    cleaned_text = ' '.join(filter(lambda x: x.strip() != '', tokenized_text_new))
    # print("Be1:", tokenized_text)
    print("Be1:", cleaned_text)
    # หลังบ่าย
    tokens = cleaned_text.split()
    modified_tokens = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token == "บ่าย" and i + 1 < len(tokens) and tokens[i + 1].isdigit():
            modified_tokens.append(f"บ่าย{tokens[i + 1]}")
            i += 2
        else:
            modified_tokens.append(token)
            i += 1
    cleaned_text = " ".join(modified_tokens)
    # print("Af1:", cleaned_text)
    # หลังทุ่ม โมง นาฬิกา เพิ่มนาที
    cleaned_text = re.sub(r'(\d+) (ทุ่ม|โมง|นาฬิกา) (\d+)', r'\1 \2 \3 นาที', cleaned_text)
    # print("Af3:", cleaned_text)
    # หลังตี
    cleaned_text = re.sub(r'ตี\s*(?=\d)', 'ตี', cleaned_text)
    # print("Af4:", cleaned_text)
    # หลังวันที่
    cleaned_text = re.sub(r'(วันที่|ที่)\s+(\d+)', r'\1\2', cleaned_text)
    # print("Af5:", cleaned_text)
    # หน้านาฬิกา นาที โมง ทุ่ม
    time_pattern = re.compile(r"(\d+)\s*(นาฬิกา|นาที|โมง|ทุ่ม)")
    matches = time_pattern.findall(cleaned_text)
    if matches:
        time_parts = []
        for match in matches:
            value = match[0]
            unit = match[1]
            time_parts.append(f"{value}{unit}")
        joined_parts = ' '.join(time_parts)
        cleaned_text = re.sub(time_pattern, joined_parts, cleaned_text)
    # print("Af2:", cleaned_text)
    for month_name, replacements in month_dict.items():
        for replacement in replacements:
            cleaned_text = cleaned_text.replace(replacement, month_name)
    # print("Af7:", cleaned_text)

    day_mapping_keys = list(day_mapping.keys())
    month_mapping_keys = list(month_key.keys())
    day_key_matches = []
    for key in day_mapping_keys:
        if key in cleaned_text:
            day_key_matches.append(key)
    month_key_matches = []
    for key in month_mapping_keys:
        if key in cleaned_text:
            month_key_matches.append(key)
    for key in month_key_matches:
        if len(day_key_matches) == 0:
            cleaned_text = re.sub(rf'(\s*)\b{key}\b', key, cleaned_text)
        else:
            break
    print("Af6:", cleaned_text)
    return cleaned_text

def find_title(text: str):
    token = modified_token(text)
    words = token.split()
    title = ' '.join([word for word in words if word not in words_mapping and word not in hour_mapping and word not in minute_mapping and word not in month_mapping and word not in day_mapping])
    time_pattern = r"\d{1,2}[:.]\d{2}"
    date_pattern = r"\d{1,2} [/] \d{1,2} [/] \d{2,4}"
    date_pattern0 = r"[/] \d{1,2} [/] \d{2,4}"
    patterns = [time_pattern, date_pattern, date_pattern0]

    for pattern in patterns:
        text = re.sub(pattern, "", title)

    time_pattern1 = r"\d{1,2}:\d{2}"
    time_pattern2 = r"\d{1,2}.\d{2}"
    nw_t1 = re.sub(time_pattern1, "", text)
    nw_t2 = re.sub(time_pattern2, "", nw_t1)

    return nw_t2.strip()

def extract_date(text: str):
    cleaned_text = modified_token(text)

    day_date = None
    month_date = None

    for word in cleaned_text.split():
        if word in day_mapping:
            day_date = int(day_mapping[word])
            break
            
    for word in cleaned_text.split():
        if word in month_mapping:
            month_date = int(month_mapping[word])
            break

    # if day_f and month_f :
    #     extracted_date = datetime(year=datetime.now().year, month=month_date, day=day_date)
    return month_date, day_date

def extract_time(text: str):
    cleaned_text = modified_token(text)

    hour_time = None
    minute_time = None

    for word in cleaned_text.split():
        if word in hour_mapping:
            hour_time = int(hour_mapping[word])
            break

    for word in cleaned_text.split():
        if word in minute_mapping:
            minute_time = int(minute_mapping[word])
            break
    else:
        minute_time = 00

    # if hour_f and minute_f:
    #     extracted_time = time(hour=hour_time, minute=minute_time)

    return hour_time, minute_time

def extract_date_time(text):
    keywords = {
        "พรุ่งนี้": 1,
        "พรุ้งนี้": 1,
        "วันหน้า": 1,
        "วันข้างหน้า": 1,
        "มะรื่น": 2,
        "อีกสองวัน": 2,
        "สัปดาห์หน้า": 7,
        "อาทิตย์หน้า": 7,
        "เดือน": 0,  # เพิ่มเดือนใน keyword ด้วยค่า 0
        "ปี": 0,    # เพิ่มปีใน keyword ด้วยค่า 0
        "วันนี้": 0  # เพิ่มคำว่า "วันนี้" โดยให้ค่าเป็น 0
    }
    pattern = re.compile("|".join(keywords.keys()))
    matches = pattern.findall(text)
    time_adjustments = {}
    for match in matches:
        if match in keywords:
            time_adjustments["day"] = keywords[match]
        elif match == "เดือนหน้า":
            time_adjustments["month"] = 1
        elif match == "ปีหน้า":
            time_adjustments["year"] = 1
    return time_adjustments

def calculate_target_date(text):
    time_adjustments = extract_date_time(text)

    # ตรวจสอบว่า "วันนี้" อยู่ในข้อความหรือไม่
    if "วันนี้" in text:
        current_date = datetime.now()
        year_date = current_date.year
        month_date = current_date.month
        day_date = current_date.day
        print(year_date, month_date, day_date)
        return year_date, month_date, day_date

    # ใช้ข้อมูลที่ได้จาก extract_date_time ในการปรับวันที่ปัจจุบัน
    target_date = datetime.now() + timedelta(days=time_adjustments.get("day", 0))
    
    if "เดือนหน้า" in text:
        current_day = datetime.now().day
        target_date = target_date.replace(day=current_day, month=target_date.month + 1)
        if target_date.month == 13:
            target_date = target_date.replace(day=1, month=1, year=target_date.year + 1)
    
    if "ปีหน้า" in text:
        target_date = target_date.replace(year=target_date.year + 1)
        
    day_date = target_date.day if "day" in time_adjustments else None
    month_date = int(target_date.strftime("%m")) if "month" in time_adjustments else int(target_date.strftime("%m"))
    year_date = target_date.year
    
    if "พรุ่งนี้" in text or "พรุ้งนี้" in text or "วันหน้า" in text or "วันหน้า" in text or \
    "วันพรุ่งนี้" in text or "วันข้างหน้า" in text or "มะรื่น" in text or "อีกสองวัน" in text or \
    "อาทิตย์หน้า" in text or "สัปดาห์หน้า" in text:  # ตรวจสอบเงื่อนไขเพิ่มเติม
        return year_date, month_date, day_date
        
    if "เดือนหน้า" in text:  # ตรวจสอบเงื่อนไขเพิ่มเติม
        return year_date, month_date, day_date  # ให้ค่าเป็น None ในช่องวัน
    
    if "ปีหน้า" in text:  # ตรวจสอบเงื่อนไขเพิ่มเติม
        return year_date, None, None # ให้ค่าเป็น None ในช่องเดือนและวัน
    
    # หากไม่มีคำใน keywords ที่ตรงกับคำในประโยค คืนค่า None ในทุกช่อง
    return year_date, None, None


def parse_sentence(text: str):
    # หาวันที่และเวลาในประโยคโดยใช้ Regular Expression
    date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'  # รูปแบบ d/m/yy, d/m/yyyy, dd/mm/yyyy
    time_pattern = r'\d{1,2}[.:]\d{2}'  # รูปแบบ HH:MM หรือ HH.MM

    # ค้นหาวันที่และเวลาจากประโยค
    date_match = re.search(date_pattern, text)
    time_match = re.search(time_pattern, text)

    day_date = None
    month_date = None
    year_date = None
    hour_time = None
    minute_time = None

    if date_match or time_match:  # ใช้เครื่องหมาย "หรือ" (or) แทน "และ" (and)
        # แยกวันที่และเวลาจากการตรงกับรูปแบบ
        date_string = date_match.group() if date_match else None
        time_string = time_match.group() if time_match else None

        # แปลงสตริงวันที่และเวลาเป็น datetime object
        if date_string:
            date_parts = re.split(r'/', date_string)
            parsed_date = None
            if len(date_parts[2]) == 2:  # ถ้าปีมี 2 หลัก
                parsed_date = datetime.strptime(date_string, '%d/%m/%y')  # รูปแบบ d/m/yy
            else:
                parsed_date = datetime.strptime(date_string, '%d/%m/%Y')  # รูปแบบ dd/mm/yyyy
        else:
            parsed_date = None

        if time_string:
            # ลองแปลงเป็นรูปแบบ HH:MM ก่อน หากไม่สำเร็จ ลองแปลงเป็นรูปแบบ HH.MM
            try:
                parsed_time = datetime.strptime(time_string, '%H:%M')  # รูปแบบ HH:MM
            except ValueError:
                parsed_time = datetime.strptime(time_string, '%H.%M')  # รูปแบบ HH.MM
        else:
            parsed_time = None

        # สร้างตัวแปรเพื่อเก็บค่าวันที่และเวลา
        date_info = {
            "year": parsed_date.strftime('%Y') if parsed_date else None,  # ใช้ strftime เมื่อมี parsed_date ไม่เป็น None
            "month": parsed_date.strftime('%m') if parsed_date else None,
            "day": parsed_date.strftime('%d') if parsed_date else None,
            "hour": parsed_time.strftime('%H') if parsed_time else None,  # ใช้ strftime เมื่อมี parsed_time ไม่เป็น None
            "minute": parsed_time.strftime('%M') if parsed_time else None
        }

        year_date = (date_info['year'])
        month_date = (date_info['month'])
        day_date = (date_info['day'])
        hour_time = (date_info['hour'])
        minute_time = (date_info['minute'])
        
        return year_date, month_date, day_date, hour_time, minute_time
    else:
        # ถ้าไม่สามารถแยกวันที่และเวลาได้
        return None, None, None, None, None

def parse_date(text: str):
    print(text)
    year1, month1, day1, hour1, minute1 = parse_sentence(text)
    year2, month2, day2 = calculate_target_date(text)
    month3, day3 = extract_date(text)
    hour2, minute2 = extract_time(text)

    year, month, day, hour, minute = None, None, None, None, None

    if year1 is not None and month1 is not None and day1 is not None:
        year, month, day = int(year1), int(month1), int(day1)
    elif month2 is not None and day2 is not None:
        year, month, day = year2, month2, day2
    elif month2 is None and day2 is None:
        year, month, day = year2, month3, day3

    if hour1 is not None and minute1 is not None:
        hour, minute = int(hour1), int(minute1)
    elif hour2 is not None and minute2 is not None:
        hour, minute = hour2, minute2

    if year is not None and month is not None and day is not None:
        if hour is not None and minute is not None:
            return year, month, day, hour, minute
        else:
            return year, month, day
    else:
        return None

res = ""

header_text_all = """
{
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "รายการกำหนดการทั้งหมด",
                "weight": "bold",
                "size": "xl"
            },
            {
                "type": "separator"
            }
        ],
        "backgroundColor": "#f7f2eb"
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
"""
header_text = """
{
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "รายการกำหนดการ",
                "weight": "bold",
                "size": "xl"
            },
            {
                "type": "separator"
            }
        ],
        "backgroundColor": "#f7f2eb"
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
"""

body_text = """
{
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [],
                  "flex": 1,
                  "backgroundColor": "COLOR_HEX",
                  "cornerRadius": "none"
                },
                {
                  "type": "box",
                  "layout": "baseline",
                  "contents": [
                    {
                      "type": "icon",
                      "url": "ICON_LINK",
                      "size": "3xl",
                      "offsetTop": "sm",
                      "offsetStart": "sm"
                    }
                  ],
                  "flex": 10
                },
                {
                  "type": "box",
                  "layout": "vertical",
                  "contents": [
                    {
                      "type": "box",
                      "layout": "horizontal",
                      "contents": [
                        {
                          "type": "text",
                          "text": "ACTIVITY_TEXT",
                          "weight": "bold",
                          "style": "normal",
                          "align": "start",
                          "gravity": "center",
                          "size": "sm"
                        }
                      ],
                      "flex": 1
                    },
                    {
                      "type": "box",
                      "layout": "horizontal",
                      "contents": [
                        {
                          "type": "text",
                          "text": "NOTIFY_TIME",
                          "flex": 3,
                          "size": "sm",
                          "color": "STATE_COLOR"

                        },
                        {
                          "type": "text",
                          "text": "ADDED_TIME",
                          "flex": 2,
                          "size": "xxs",
                          "style": "italic"
                        }
                      ]
                    }
                  ],
                  "flex": 50,
                  "offsetStart": "sm"
                }
              ]
            },
            {
              "type": "separator"
            }
          ]
        }
"""

footer_text = """
        ],
        "backgroundColor": "#f7f2eb"
    }
}
"""

list_empty = """{
  "type": "bubble",
  "body": {
    "type": "box",
    "layout": "vertical",
    "contents": [
      {
        "type": "text",
        "text": "คุณยังไม่ได้บันทึกกำหนดการค่ะ"
      }
    ],
    "backgroundColor": "#f7f2eb"
  }
}"""

def is_notification_time(current_time, user_time=None):
    minutes = current_time.tm_min
    seconds = current_time.tm_sec
    user_minutes = int(user_time.split(":")[1]) if user_time else None

    if user_time:
        if minutes == user_minutes and seconds == 0:
            return True

    if user_minutes:
        if minutes >= user_minutes and minutes < user_minutes + 15:
            return True

        return False

    while True:
        current_time = time.localtime()
        user_input_time = input("Enter a time (HH:MM) for immediate notification or press Enter: ")

        # Check if it's time for immediate notification
        if user_input_time and len(user_input_time) == 5:
            if is_notification_time(current_time, user_input_time):
                print("Immediate notification at", user_input_time)

        # Check if it's time for a regular notification (every 15 minutes)
        elif is_notification_time(current_time):
            print("Notification at", time.strftime("%H:%M", current_time))

        time.sleep(1)  # Sleep for 1 second

def test(tx : str):
    tx = " "
    return tx

# def init_process_notify(text : str):

#     #Theard --> call process_notify

#     thr = threading.Thread(target=process_notify(text))
#     thr.start()
#     # callback
#     return True

# def process_notify(tx : str):
#     #do every here
#     while(True):
#         #do something
#         test(tx)
#         time.sleep(120)  # min
#         return True


# init_process_notify()
# try except: pass
