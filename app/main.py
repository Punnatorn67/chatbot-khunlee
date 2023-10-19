from fastapi import FastAPI, Header, Request,Form
from fastapi.responses import PlainTextResponse, JSONResponse, Response
from datetime import datetime, timedelta, time
import time as time_r
import pymongo
import pytz
import json
from app import predict_text, parse_date, find_title, header_text_all, header_text, body_text, footer_text, list_empty
import threading
import shlex
import subprocess

global db

app = FastAPI(
  title = "Service API",
  description = "My Service API",
  version= "0.1.0",
)

with open("file/color_hex.json", "r", encoding="utf-8") as file:
  color_mapping = json.load(file)
with open("file/label.json", "r", encoding="utf-8") as file:
  label_mapping = json.load(file)

client = pymongo.MongoClient('mongodb://khunlee-mongo:27017/')
db = client['khunlee']

print("DB >", db)

@app.get("/")
def read_root():
  response_text = "<h3 style='font-size: 84px;'>u won't break my soul ♡♡</h3>"

  return PlainTextResponse(content=response_text, media_type="text/html")

@app.get("/insert")
async def insert(text: str, userid: str):

  title = find_title(text)
  label = predict_text(title)
  
  parsed_date = parse_date(text)
  # if parsed_date is None:
  #   pls = 'เนื่องจากข้อมูลไม่ครบถ้วนจึงไม่สามารถสร้างกำหนดการได้ค่ะ\n\nโปรดป้อนกำหนดการใหม่นะคะ'
  #   return PlainTextResponse(content=pls)  
  try:
    year, month, day, hour, minute = parsed_date
    extracted_date = datetime(year=year, month=month, day=day)
    extracted_time = time(hour=hour, minute=minute)
    extracted_datetime = datetime(year, month, day, hour, minute)
  except (ValueError, TypeError):
    pls = 'เนื่องจากข้อมูลไม่ครบถ้วนจึงไม่สามารถสร้างกำหนดการได้ค่ะ\n\nโปรดป้อนกำหนดการใหม่นะคะ'
    return PlainTextResponse(content=pls)  

  global db

  thai_timezone = pytz.timezone('Asia/Bangkok')
  thai_timestamp = datetime.now(thai_timezone)
  thai_timestamp = thai_timestamp.strftime("%Y-%m-%d %H:%M:%S")
  obj = {
    "user_id": userid,
    "text": text,
    "title": title,
    "label": label,
    "time": extracted_datetime,
    "timestamp": thai_timestamp,
  }

  res = db.schedule.insert_one(obj)
  response_text = f"{label}:\n{extracted_date}\n{extracted_time}\n{extracted_datetime}"
  print(response_text)
  res_text = 'สร้างกำหนดการเรียบร้อยค่ะ'
  
  return PlainTextResponse(content=res_text)

@app.get("/find")
async def find(userid: str):
  obj = list(db.schedule.find({'user_id': userid}).sort([('time', 1)]))
  print(obj)
  return PlainTextResponse(content=obj)

@app.get("/activity-all")
def list_flex(userid: str):
  obj = list(db.schedule.find({'user_id': userid}).sort([('time', 1)]))

  print(obj)
  if not obj:
    res = list_empty
    return PlainTextResponse(content=res)
  else:
    body_list = []
    for o in obj:
      print(o)
      title = o['title']
      xx = predict_text(title)
      print(xx)
      time = o['time']
      current_time = datetime.now(pytz.timezone('Asia/Bangkok'))
      formatted_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")
      formatted_datetime = datetime.strptime(formatted_datetime, '%Y-%m-%d %H:%M:%S')

      if time < formatted_datetime:
        state_color = "#de222d"
      else:
        state_color = "#13955f" #"#2dde22"

      format_time = time.strftime('%d/%m, %H:%M')
      timestamp = o['timestamp']
      timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
      format_timestamp = timestamp.strftime('%d/%m, %H:%M')
      label = o['label']
      activity_text = title
      notify_time = format_time
      added_time = format_timestamp
      color_hex = color_mapping.get(label)
      icon_url = label_mapping.get(label)

      body_text_tmp = body_text
      body_text_tmp = body_text_tmp.replace("COLOR_HEX", color_hex)
      body_text_tmp = body_text_tmp.replace("ICON_LINK", icon_url)
      body_text_tmp = body_text_tmp.replace("ACTIVITY_TEXT", activity_text)
      body_text_tmp = body_text_tmp.replace("NOTIFY_TIME", str(notify_time))
      body_text_tmp = body_text_tmp.replace("STATE_COLOR", state_color)
      body_text_tmp = body_text_tmp.replace("ADDED_TIME", str(added_time))
      body_list.append(body_text_tmp)
      res = header_text_all+" "+",".join(body_list)+" "+footer_text
  return PlainTextResponse(content=res)

@app.get("/activity-sort")
def sort_flex(userid: str):
  current_time = datetime.now(pytz.timezone('Asia/Bangkok'))
  formatted_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")
  formatted_datetime = datetime.strptime(formatted_datetime, '%Y-%m-%d %H:%M:%S')
  obj = list(db.schedule.find({'user_id': userid, "time": {"$gt": formatted_datetime}}).sort([('time', 1)]))
  print(obj)
  if not obj:
    res = list_empty
    return PlainTextResponse(content=res)
  body_list = []

  for o in obj:
    title = o['title']
    time = o['time']
    current_time = datetime.now(pytz.timezone('Asia/Bangkok'))
    formatted_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_datetime = datetime.strptime(formatted_datetime, '%Y-%m-%d %H:%M:%S')

    if time < formatted_datetime:
        state_color = "#de222d"
    else:
        state_color = "#13955f" #"#2dde22"

    format_time = time.strftime('%d/%m, %H:%M')
    timestamp = o['timestamp']
    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    format_timestamp = timestamp.strftime('%d/%m, %H:%M')
    label = o['label']
    activity_text = title
    notify_time = format_time
    added_time = format_timestamp
    color_hex = color_mapping.get(label)
    icon_url = label_mapping.get(label)

    body_text_tmp = body_text
    body_text_tmp = body_text_tmp.replace("COLOR_HEX", color_hex)
    body_text_tmp = body_text_tmp.replace("ICON_LINK", icon_url)
    body_text_tmp = body_text_tmp.replace("ACTIVITY_TEXT", activity_text)
    body_text_tmp = body_text_tmp.replace("NOTIFY_TIME", str(notify_time))
    body_text_tmp = body_text_tmp.replace("STATE_COLOR", state_color)
    body_text_tmp = body_text_tmp.replace("ADDED_TIME", str(added_time))
    body_list.append(body_text_tmp)
    
  res = header_text+" "+",".join(body_list)+" "+footer_text
  return PlainTextResponse(content=res)

@app.get("/delete-all")
async def delete_all(userid :str):
    # กำหนดเงื่อนไขการลบเป็นเงื่อนไขที่ไม่มีให้ลบทั้งหมด
    deletion_criteria = {}
    
    # ดำเนินการลบข้อมูลทั้งหมด
    delete_result = db.schedule.delete_many({'user_id': userid},deletion_criteria)
    
    # ตรวจสอบจำนวนเอกสารที่ถูกลบ
    num_deleted = delete_result.deleted_count
    if num_deleted > 0:
      response_message = f"ลบกำหนดการทั้งหมด (จำนวน {num_deleted} รายการ) เรียบร้อยแล้วค่ะ"
    else:
      response_message = f"คุณยังไม่ได้บันทึกกำหนดการค่ะ"
    
    return PlainTextResponse(content=response_message)

def send_notify(user_id:str,msg:str):
  line_token = "UixJDE9F0y35C56Cy6tU5sXQ6FauQLsTjmh5ok8ZvDXu+nttsLWdwIRrqmsgzFEjFuVIVRYR4mzAcnvPcPTThdwxabJtOyQ50vgLJqYdYFcVzfTispvUM2oxSU6bCYoa4llxSZeoddOsEzXJDs+zBQdB04t89/1O/w1cDnyilFU="
  api_endpoint = "https://api.line.me/v2/bot/message/push"

  cmd = """

  curl -v -X POST https://api.line.me/v2/bot/message/push \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer LINE_ACCESS_TOKEN' \
  -d '{
      "to": "USER_ID_TEXT",
      "messages":[
          {
              "type":"text",
              "text":"MESSAGE_TEXT"
          }
      ]
  }'                          
  """

  cmd = cmd.replace("LINE_ACCESS_TOKEN",line_token).replace("USER_ID_TEXT",user_id).replace("MESSAGE_TEXT",msg)
  command = shlex.split(cmd)

  process = subprocess.run(command,capture_output=True,text=True)

  return process.stdout

# เรียกใช้ฟังก์ชั่นนี้ทุกๆ15นาที
def next_time():
    print('do next time')
    while True: # ลูปเพื่อทำการแจ้งเตือน
      current_time = datetime.now(pytz.timezone('Asia/Bangkok'))
      formatted_datetime = current_time.strftime("%Y-%m-%d %H:%M:%S")
      formatted_datetime = datetime.strptime(formatted_datetime, '%Y-%m-%d %H:%M:%S')
      y = formatted_datetime.year
      mo = formatted_datetime.month
      d = formatted_datetime.day
      h = formatted_datetime.hour
      m = formatted_datetime.minute

      # query มาแล้วมาคำนวณเพื่อแจ้งเตือนก่อน 15 นาที mod เพื่อหานาทีใน quater
      cq = int(m / 15) # เอานาทีมา 15  mod
      xq = cq + 1 # เอาผล mod มา + 1 เพื่อเอาจุดที่ไม่ใช่ query
      nt = xq * 15 # เพื่อหาเวลาที่จะ query แปลงเป็นหน่วยนาที

      if nt == 60: #เป็นการ + ชม ไป
        h += 1
        nt = 0

# 
      nqd = datetime(y, mo, d, h, nt) # start range
      end_time = nqd + timedelta(minutes=15)# End range
      q = {'time': {"$gte": nqd, "$lt": end_time}}# หา เวลาที่จะแจ้งเตือนใน range
      obj = list(db.schedule.find(q))


      print(len(obj),q)

      if not obj:
        print("No upcoming activities in the next 15 minutes.")
        time_r.sleep(900)  # รอ 15 นาทีก่อนที่จะทำการตรวจสอบอีกครั้ง
      else:
        notify_text = {"user_id": "USER_ID_TEXT", "text": "ใกล้ถึงกำหนดการ TITLE_TEXT (เวลา NOTIFY_TIME) ของคุณแล้ว"}
        data_list = []

        for o in obj: #loop to notify to user
          title = o['title']
          userid = o['user_id']
          time = o['time']
          format_time = time.strftime('%d/%m, %H:%M')
          activity_text = title
          notify_time = format_time
          notification = {
            "user_id": userid,
            "text": notify_text["text"].replace("TITLE_TEXT", activity_text).replace("NOTIFY_TIME", str(notify_time).replace("USER_ID_TEXT",userid))
          }
          data_list.append(notification)
          send_notify(userid,notification['text'])
          time_r.sleep(900)

        res_str = '\n'.join([notification["text"] for notification in data_list])
        print(data_list)
        return res_str  # คืนค่าและรอ 2 นาทีก่อนที่จะทำการตรวจสอบอีกครั้ง
      

# อันนี้จะใช้ cronjob เพื่อมา trigger api นี้ เพื่อไปแจ้งเตือน
@app.get("/start_next_time")
async def start_next_time():
    print('start next time')
    result = True
    # result = await next_time(userid)
    # ทำอะไรสักอย่างกับ result ก่อนคืนให้ผู้ใช้
    thread = threading.Thread(target=next_time)
    thread.start()
    return {"result": result}

