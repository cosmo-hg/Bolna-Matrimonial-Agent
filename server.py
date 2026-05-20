import os
from datetime import datetime
from flask import Flask, request, jsonify
import gspread
import pytz
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# ── Google Sheets config ─────────────────────────────────────────────────────
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
SHEET_ID   = os.getenv("GOOGLE_SHEET_ID")
CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
HEADERS    = ["Timestamp", "Execution ID", "Status", "Duration (sec)",
              "Outcome", "Flag for Callback", "Recording URL", "Transcript Summary"]

def get_sheet():
    creds  = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

# ── Add headers if sheet is empty ────────────────────────────────────────────
def ensure_headers(sheet):
    if not sheet.row_values(1):
        sheet.append_row(HEADERS, value_input_option="USER_ENTERED")

# ── Outcome classifier from transcript keywords ──────────────────────────────
def classify(transcript: str) -> tuple[str, str]:
    t = transcript.lower()
    if "relationship manager" in t:
        return "Wants Callback", "YES"
    if "already married" in t or "got married" in t:
        return "DEACTIVATE", "NO"
    if "whatsapp" in t:
        return "Reminder Sent", "NO"
    if "cancel" in t or "refund" in t:
        return "Escalate to Support", "YES"
    return "Completed", "NO"

# ── Webhook endpoint ─────────────────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}

    execution_id  = data.get("execution_id",  "N/A")
    transcript    = data.get("transcript",     "")
    duration      = data.get("duration",       0)
    status        = data.get("status",         "unknown")
    recording_url = data.get("recording_url",  "")

    outcome, flag = classify(transcript)

    ist       = pytz.timezone("Asia/Kolkata")
    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
    summary   = transcript[:250].replace("\n", " ")

    row = [timestamp, execution_id, status, duration,
           outcome, flag, recording_url, summary]

    # ── Append to Google Sheet ───────────────────────────────────────────────
    try:
        sheet = get_sheet()
        ensure_headers(sheet)
        sheet.append_row(row, value_input_option="USER_ENTERED")
        print(f"[{timestamp}] Logged: {execution_id} | {outcome} | flag={flag}")
    except Exception as e:
        print(f"ERROR writing to Google Sheet: {e}")
        return jsonify({"status": "sheet_error", "detail": str(e)}), 500

    return jsonify({"status": "logged"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=False)
