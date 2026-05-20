# Bolna Matrimonial Voice Agent — Priya

A voice AI agent that calls Shaadi.com members who have not logged in recently, nudges them to check their pending match interests, and logs every outcome automatically.

## Demo Recording

<video src="https://github.com/user-attachments/assets/e3896429-34a7-4e25-849d-4006723a7532" controls width="100%"></video>

---

## The Shaadi.com Use Case

### The Problem

Shaadi.com has tens of millions of profiles. When a premium member receives new match interests, the platform sends an app notification or email. Most go ignored. The member either forgot they signed up, lost interest, or is simply not checking the app regularly.

Shaadi's sales team manually calls premium members to nudge them to respond to matches and renew engagement. At scale this means hundreds of calls per day, inconsistent follow-up timing, no coverage in Hindi or regional languages, and sales reps spending most of their time on "did you see your matches?" calls instead of higher value conversations.

There is no public evidence of Shaadi.com or any major matrimonial platform using voice AI for this workflow. It is a greenfield opportunity directly parallel to what Bolna already does for Hyreo in recruitment: automated follow-up calls for a people-matching use case.

### The Solution

A Bolna voice agent called Priya automatically calls premium members who have not logged in for several days and have pending match interests. Priya speaks in natural English or Hinglish, tells the member about their pending matches, and nudges them to check the app. If the member is frustrated about match quality, Priya offers a human relationship manager callback. If they want to cancel, Priya escalates to the support team. Every call outcome is logged automatically to Google Sheets including the call duration, transcript summary, and a recording URL for review.

### The Impact

A human sales rep can make 50 to 80 calls per day. This agent handles unlimited concurrent calls, responds within minutes of a trigger firing, and operates in Hindi or Hinglish without any additional setup. Members who previously went uncontacted due to bandwidth constraints now receive a timely, personalised follow-up in their preferred language.

---

## Architecture

```
trigger.py  ──►  Bolna API  ──►  Plivo (PSTN)  ──►  Member's phone
                     │
          Deepgram (STT) + ElevenLabs TTS (Nila voice)
                     │
              Webhook POST
                     │
              server.py (Flask)
                     │
              Google Sheets (call log)
```

---

## Project Structure

```
shaadi-bolna-demo/
├── setup.py          # Registers the Priya agent on Bolna (run once)
├── trigger.py        # Fires an outbound call
├── server.py         # Flask webhook — logs outcome to Google Sheets
├── prompt.txt        # Voice agent system prompt
├── mock_members.json # Sample member data for testing
├── demo/
│   └── priya-demo-call.m4a   # Sample call recording
├── .env.example      # Environment variable template
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Python 3.10+
- [Bolna](https://bolna.dev) account with API key
- [ngrok](https://ngrok.com) (free tier) for local webhook exposure
- Google Cloud service account with Sheets API and Drive API enabled
- A Google Sheet shared with the service account

---

## Setup

**1. Install dependencies**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**2. Configure environment**
```bash
cp .env.example .env
```
Fill in `.env` with your Bolna API key, phone number, Google Sheet ID, and credentials file path.

**3. Add Google credentials**

Download your service account JSON from Google Cloud Console, save it as `credentials.json` in this folder, and share your Google Sheet with the service account email as Editor.

**4. Start ngrok**
```bash
ngrok http 5000
```

**5. Register the agent (one-time)**
```bash
python setup.py
```
Paste your ngrok URL when prompted. `BOLNA_AGENT_ID` is written to `.env` automatically.

---

## Running the Demo

**Terminal 1 — webhook server**
```bash
python server.py
```

**Terminal 2 — trigger a call**
```bash
python trigger.py --index 0   # live call to your number
python trigger.py --index 1   # mock: Aravind Krishnamurthy
python trigger.py --index 2   # mock: Nisha Patel
```

---

## Edge Cases Handled

| Member Says | Outcome | Flagged |
|---|---|---|
| Asks about match details | Priya shares name, age, profession naturally | No |
| Wants a relationship manager | Flags for callback | Yes |
| Already married / got married | Congratulates, flags for deactivation | No |
| Asks for WhatsApp reminder | Confirms and closes warmly | No |
| Wants to cancel or refund | Escalates to support | Yes |
| Asks if Priya is a bot | Deflects and redirects | No |
| Speaks only Hindi | Full Hindi response | No |

---

## Google Sheet Columns

| Column | Description |
|---|---|
| Timestamp | IST timestamp of the call |
| Execution ID | Bolna call identifier |
| Status | Call status from Bolna |
| Duration (sec) | Call length |
| Outcome | Classified result |
| Flag for Callback | YES / NO |
| Recording URL | Link to call recording |
| Transcript Summary | First 250 characters of transcript |

---

## Security

All sensitive values (API keys, phone numbers, credentials) live exclusively in `.env` and `credentials.json`. Both are listed in `.gitignore` and are never committed. The `.env.example` file contains only placeholder values and is safe to share.
