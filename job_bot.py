import os
import urllib.request
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone


# Delete existing config.json if exists
if os.path.exists("config.json"):
    os.remove("config.json")

# Download config.json from GitHub
url = "https://raw.githubusercontent.com/sisyphusinthegit/job-bot/main/config.json"
urllib.request.urlretrieve(url, "config.json")


# Create a function that loads the config
def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)


#  Create a function that sends the email notification

def send_email(subject, body):
    config = load_config()
    email_conf = config["email"]

    msg = MIMEMultipart()
    msg["From"] = email_conf["sender_email"]
    msg["To"] = email_conf["receiver_email"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(email_conf["smtp_server"], email_conf["smtp_port"]) as server:
        server.starttls()
        server.login(email_conf["sender_email"], email_conf["sender_password"])
        server.send_message(msg)

    print("Email is sent successfully.")

#  Create a function that sends the telegram notification

def send_telegram(message):
  config = load_config()
  token = config["telegram"]["bot_token"]
  chat_id = config["telegram"]["chat_id"]

  url = f"https://api.telegram.org/bot{token}/sendMessage"
  payload = {
      "chat_id" : chat_id,
      "text": message
  }

  response = requests.post(url, data= payload)

  if response.status_code == 200:
    print("Message is sent successfully.")
  else:
    print(f"Error: {response.status_code} - {response.text}")

# Combine notification functions together

def notification(subject, message):
  try:
    send_email(subject, message)
  except Exception as excep:
    print(f"Email Error: {excep}")

  try:
    send_telegram(message)
  except Exception as excep:
    print(f"Telegram Error: {excep}")


# Create a function that gets the remote jobs

def remote_jobs():
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        jobs = response.json()
        return jobs[1:]
    else:
        print(f"Error: {response.status_code}")
        return []



def relevant_job(job, config):
    title = job.get("position", "").lower()
    job_date_str = job.get("date", "")
    

    if not any(kw.lower() in title for kw in config["search_keywords"]):
        return False

    try:
        job_time = datetime.strptime(job_date_str, "%Y-%m-%dT%H:%M:%S%z")
        if datetime.now(timezone.utc) - job_time > timedelta(hours=500):
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

    return True



jobs = remote_jobs()
config = load_config()

for job in jobs:
    if relevant_job(job, config):
        message = f" {job['position']} @ {job.get('company', 'Unknown')}\n {job.get('location', 'Remote')}\n🔗 {job.get('url', '')}"
        notification("New Job Post!", message)
