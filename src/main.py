import requests
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import time
from telegram import Bot
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")
URL = "https://internship.cse.hcmut.edu.vn/"
DATA_FILE = "../companies.txt"

bot_token = os.getenv("BOT_TOKEN")  
chat_id = os.getenv("CHAT_ID")
if not bot_token or not chat_id:
  raise ValueError("Please set the BOT_TOKEN and CHAT_ID environment variables.")

def send_telegram_message(bot_token, chat_id, message):
  bot = Bot(token=bot_token)
  bot.send_message(chat_id=chat_id, text=message)

def print_companies(res):
  item = res["item"]
  message = (
      "🏢 *{fullname}* (`{shortname}`)\n"
      "📍 Địa chỉ: {address}\n"
      "👥 Số sinh viên nhận tối đa: {maxAcceptedStudent}\n"
      "📝 Đã đăng ký: {studentRegister}/{maxRegister}\n"
      "✅ Đã nhận: {studentAccepted}\n"
      "------------------------------------------------------\n"
  ).format(
      fullname=item["fullname"],
      shortname=item["shortname"],
      address=item["address"],
      maxAcceptedStudent=item["maxAcceptedStudent"],
      studentRegister=item["studentRegister"],
      maxRegister=item["maxRegister"],
      studentAccepted=item["studentAccepted"],
  )
  if item["maxAcceptedStudent"] - item["studentAccepted"] > 0:
    if item["maxRegister"] - item["studentRegister"] > 0:
      message += "🔥 *Còn slot, bú lẹ!* 🔥"
      return [True, message]
  return [False, message]

def send_telegram_message(bot_token, chat_id, message):
  url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
  payload = {
      "chat_id": chat_id,
      "text": message,
      "parse_mode": "Markdown"
  }
  response = requests.post(url, data=payload)
  return response.ok

def check_available():
  figures = fetch_companies(URL)
  new_companies_id = [figure["data-id"] for figure in figures]
  available_companies = []
  for id in new_companies_id:
    detail = fetch_companies_detail(id)
    res = print_companies(detail)
    if res[0]:
      available_companies.append(detail["item"]["fullname"])
  if available_companies:
    print("Các công ty còn slot:")
    for company in available_companies:
      print(company)
  else:
    print("Không có công ty nào còn slot")
  

def fetch_companies(url):
  options = Options()
  options.add_argument("--headless")  # nếu muốn chạy ẩn
  options.add_argument("--disable-gpu")
  driver = webdriver.Edge(service=Service(), options=options)
  try:
    driver.get(url)
    time.sleep(3)  
    soup = BeautifulSoup(driver.page_source, "html.parser")
    figures = soup.select("figure[data-id]")
  finally:
    driver.quit()
  return figures

def fetch_companies_detail(company_id):
  timestamp = int(time.time() * 1000)  # để tránh cache
  url = f"https://internship.cse.hcmut.edu.vn/home/company/id/{company_id}?t={timestamp}"
  try:
    response = requests.get(url)
    if response.status_code == 200:
      return response.json()
    else:
      print(f"Error fetching company details: {response.status_code}")
  except requests.RequestException as e:
    print(f"Request failed: {e}")

def load_old_companies(path):
  if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
      return f.read().splitlines()
  return []

def save_companies(path, figures):
  with open(path, "w", encoding="utf-8") as f:
    for figure in figures:
      f.write(figure["data-id"].strip() + "\n")
  
def main():
  old_companies_id = load_old_companies(DATA_FILE)
  figures = fetch_companies(URL)
  new_companies_id = [figure["data-id"] for figure in figures]
  new_companies = set(new_companies_id) - set(old_companies_id)
  msg = ""
  if new_companies:
    msg += "Có công ty mới:\n"
    for c in new_companies:
      res = print_companies(fetch_companies_detail(c))
      msg +=res[1]
    send_telegram_message(bot_token, chat_id, msg)
    save_companies(DATA_FILE, figures)
  else:
    print("No new companies found.")

if __name__ == "__main__":
  while True:
    print("Running at", time.strftime("%Y-%m-%d %H:%M:%S"))
    main()
    time.sleep(600)
  # check_available()