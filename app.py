import streamlit as st
import datetime
import pickle
import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']

# ฟังก์ชันสร้าง OAuth Flow จาก secrets.toml
def create_flow():
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["client_id"],
                "client_secret": st.secrets["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [st.secrets["redirect_uri"]],
            }
        },
        scopes=SCOPES,
        redirect_uri=st.secrets["redirect_uri"]
    )

# สร้างลิงก์ให้ผู้ใช้ล็อกอิน
def generate_auth_url(flow):
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    return auth_url

# ฟังก์ชันสร้าง service จาก credentials
def create_service(creds):
    return build("calendar", "v3", credentials=creds)

# ฟังก์ชันหลัก
def main():
    st.title("🗓️ เพิ่มกิจกรรมลง Google Calendar (Online)")

    # เช็คว่ามี credentials แล้วหรือยัง
    if "credentials" not in st.session_state:
        flow = create_flow()
        auth_url = generate_auth_url(flow)
        st.markdown(f"[🔐 ล็อกอินด้วย Google]({auth_url})")
        code = st.text_input("วางรหัสจาก URL ที่คุณได้รับหลังล็อกอิน (พารามิเตอร์ `?code=...`):")

        if code:
            try:
                flow.fetch_token(code=code)
                creds = flow.credentials
                st.session_state["credentials"] = {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes
                }
                st.success("🎉 ล็อกอินสำเร็จ! สามารถเพิ่มกิจกรรมได้แล้ว")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        return

    # ใช้ credentials ที่อยู่ใน session
    creds = Credentials(**st.session_state["credentials"])

    # แบบฟอร์มเพิ่มกิจกรรม
    with st.form("event_form"):
        summary = st.text_input("หัวข้อกิจกรรม", "ประชุมทีม")
        location = st.text_input("สถานที่", "Google Meet")
        start_date = st.date_input("วันที่เริ่ม")
        end_date = st.date_input("วันที่สิ้นสุด")
        submitted = st.form_submit_button("เพิ่มกิจกรรม")

    if submitted:
        service = create_service(creds)
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
        st.success(f"✅ เพิ่มกิจกรรมสำเร็จ: [คลิกดูใน Calendar]({created_event.get('htmlLink')})")

if __name__ == "__main__":
    main()
