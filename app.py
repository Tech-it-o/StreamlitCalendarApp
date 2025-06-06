import streamlit as st
import datetime
import json
import os
import pathlib
import uuid

from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = "https://your-app-name.streamlit.app"  # เปลี่ยนเป็นชื่อ app จริง

def get_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["client_id"],
                "client_secret": st.secrets["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

# 1. Step 1 - Login
if "credentials" not in st.session_state:
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    st.markdown(f"[🔐 ล็อกอินด้วยบัญชี Google เพื่อใช้งาน Calendar]({auth_url})")
    code = st.text_input("🔑 วางโค้ด (code) จากลิงก์ Google ที่ได้หลังจากล็อกอิน:")
    if st.button("ยืนยันโค้ด"):
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            st.session_state.credentials = json.loads(creds.to_json())
            st.success("✅ ล็อกอินสำเร็จ!")
        except Exception as e:
            st.error(f"❌ ล็อกอินล้มเหลว: {e}")
    st.stop()

# 2. Step 2 - Add calendar event
creds = Credentials.from_authorized_user_info(st.session_state.credentials)
service = build("calendar", "v3", credentials=creds)

st.title("📆 เพิ่มกิจกรรมลง Google Calendar ของคุณ")

with st.form("event_form"):
    summary = st.text_input("หัวข้อกิจกรรม", "ประชุมทีม")
    location = st.text_input("สถานที่", "Google Meet")
    start_date = st.date_input("วันที่เริ่ม")
    end_date = st.date_input("วันที่สิ้นสุด")
    submitted = st.form_submit_button("เพิ่มกิจกรรม")

if submitted:
    event = {
        'summary': summary,
        'location': location,
        'start': {
            'date': start_date.strftime("%Y-%m-%d"),
            'timeZone': 'Asia/Bangkok',
        },
        'end': {
            'date': end_date.strftime("%Y-%m-%d"),
            'timeZone': 'Asia/Bangkok',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    st.success(f"✅ เพิ่มกิจกรรมเรียบร้อย! [ดูใน Calendar]({created_event.get('htmlLink')})")
