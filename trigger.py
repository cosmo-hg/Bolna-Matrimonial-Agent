import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Args ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Trigger a Priya call to a Shaadi member")
parser.add_argument("--index", type=int, default=0, help="Member index (0=demo, 1-2=mock)")
args = parser.parse_args()

# ── Load env vars ────────────────────────────────────────────────────────────
API_KEY  = os.getenv("BOLNA_API_KEY")
AGENT_ID = os.getenv("BOLNA_AGENT_ID")

if not API_KEY or not AGENT_ID:
    print("ERROR: BOLNA_API_KEY and BOLNA_AGENT_ID must be set in .env")
    sys.exit(1)

# ── Load mock member data ────────────────────────────────────────────────────
with open("mock_members.json", "r", encoding="utf-8") as f:
    members = json.load(f)

if args.index < 0 or args.index >= len(members):
    print(f"ERROR: --index must be 0–{len(members) - 1}")
    sys.exit(1)

member = members[args.index]

# ── Build user_data: index 0 uses real name/phone from .env ─────────────────
if args.index == 0:
    demo_name  = os.getenv("DEMO_MEMBER_NAME")
    demo_phone = os.getenv("DEMO_MEMBER_PHONE")
    if not demo_name or not demo_phone:
        print("ERROR: DEMO_MEMBER_NAME and DEMO_MEMBER_PHONE must be set in .env")
        sys.exit(1)
    recipient_phone = demo_phone
    user_data = {
        "member_name":      demo_name,
        "match_count":      member["match_count"],
        "membership_type":  member["membership_type"],
        "last_login":       member["last_login"],
        "match_details":    member["match_details"]
    }
else:
    # Placeholder phones — no real call will connect
    recipient_phone = member["phone"]
    user_data = {
        "member_name":      member["member_name"],
        "match_count":      member["match_count"],
        "membership_type":  member["membership_type"],
        "last_login":       member["last_login"],
        "match_details":    member["match_details"]
    }

# ── Fire the call via Bolna API ──────────────────────────────────────────────
payload = {
    "agent_id":               AGENT_ID,
    "recipient_phone_number": recipient_phone,
    "user_data":              user_data
}

try:
    resp = requests.post(
        "https://api.bolna.ai/call",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    result       = resp.json()
    execution_id = result.get("execution_id") or result.get("call_id") or "unknown"
    print(f"Call triggered successfully.")
    print(f"Recipient : {recipient_phone}")
    print(f"Member    : {user_data['member_name']}")
    print(f"Execution : {execution_id}")
except requests.RequestException as e:
    print(f"ERROR triggering call: {e}")
    sys.exit(1)
