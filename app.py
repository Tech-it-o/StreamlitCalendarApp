import streamlit as st
import datetime
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

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

def generate_auth_url(flow):
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline', include_granted_scopes='true')
    return auth_url

def create_service(creds):
    return build("calendar", "v3", credentials=creds)

def main():
    st.title("🗓️ เพิ่มกิจกรรมลง Google Calendar (Online)")

    # ดึง query params
    params = st.experimental_get_query_params()
    code = params.get("code", [None])[0]

    # ถ้ายังไม่ได้ login
    if "credentials" not in st.session_state:
        code = st.text_input("📥 วางรหัส code จาก URL (พารามิเตอร์ `?code=...`):")

        if code:
            try:
                flow = create_flow()
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
                st.success("🎉 ล็อกอินสำเร็จ! พร้อมใช้งานแล้ว")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
        else:
            flow = create_flow()
            auth_url = generate_auth_url(flow)
            st.markdown(f"### 🔐 ยังไม่ได้ล็อกอิน")
            st.markdown(f"[👉 คลิกเพื่อเข้าสู่ระบบด้วย Google]({auth_url})")
            st.stop()


    # ถ้า login แล้ว
    creds = Credentials(**st.session_state["credentials"])
    service = create_service(creds)

    with st.form("event_form"):
        summary = st.text_input("หัวข้อกิจกรรม", "ประชุมทีม")
        location = st.text_input("สถานที่", "Google Meet")
        start_date = st.date_input("วันที่เริ่ม", datetime.date.today())
        end_date = st.date_input("วันที่สิ้นสุด", datetime.date.today())
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
        st.success(f"✅ เพิ่มกิจกรรมสำเร็จ: [คลิกดูใน Calendar]({created_event.get('htmlLink')})")

if __name__ == "__main__":
    main()
