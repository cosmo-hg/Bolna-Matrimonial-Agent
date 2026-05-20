import os, sys, requests
from dotenv import load_dotenv

load_dotenv()

# ── Validate required env var ────────────────────────────────────────────────
API_KEY = os.getenv("BOLNA_API_KEY")
if not API_KEY:
    print("ERROR: BOLNA_API_KEY not set in .env"); sys.exit(1)

# ── Load system prompt ───────────────────────────────────────────────────────
with open("prompt.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

# ── Prompt for ngrok webhook URL (paste before running) ─────────────────────
webhook_url = input("Paste your ngrok webhook URL (e.g. https://xxxx.ngrok.io/webhook): ").strip()

# ── Build agent payload ──────────────────────────────────────────────────────
payload = {
    "agent_config": {
        "agent_name": "Priya - Shaadi Member Success",
        "agent_type": "other",
        "webhook_url": webhook_url,
        "tasks": [{
            "task_type": "conversation",
            "toolchain": {"execution": "sequential", "pipelines": [["transcriber", "llm", "synthesizer"]]},
            "tools_config": {
                "llm_agent": {
                    "agent_type": "simple_llm_agent",
                    "agent_flow_type": "streaming",
                    "llm_config": {
                        "provider": "openai", "family": "openai", "model": "gpt-4.1",
                        "max_tokens": 150, "temperature": 0.1
                    }
                },
                "synthesizer": {
                    "provider": "elevenlabs",
                    "provider_config": {"voice": "Nila", "voice_id": "V9LCAAi4tTlqe9JadbCo", "model": "eleven_turbo_v2_5"},
                    "stream": True, "buffer_size": 250, "audio_format": "wav"
                },
                "transcriber": {
                    "provider": "deepgram", "model": "nova-2", "language": "hi",
                    "stream": True, "sampling_rate": 16000, "encoding": "linear16", "endpointing": 250
                },
                "input":  {"provider": "plivo", "format": "wav"},
                "output": {"provider": "plivo", "format": "wav"}
            },
            "task_config": {"hangup_after_silence": 10, "call_terminate": 120, "backchanneling": True}
        }]
    },
    "agent_prompts": {"task_1": {"system_prompt": system_prompt}}
}

# ── POST to Bolna to create the agent ───────────────────────────────────────
try:
    resp = requests.post(
        "https://api.bolna.ai/v2/agent",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json=payload, timeout=30
    )
    resp.raise_for_status()
    agent_id = resp.json().get("agent_id") or resp.json().get("id")
    if not agent_id:
        print(f"ERROR: agent_id missing in response: {resp.json()}"); sys.exit(1)
except requests.RequestException as e:
    print(f"ERROR creating agent: {e}"); sys.exit(1)

# ── Write agent_id back into .env ────────────────────────────────────────────
with open(".env", "r") as f:
    lines = f.readlines()
with open(".env", "w") as f:
    for line in lines:
        f.write(f"BOLNA_AGENT_ID={agent_id}\n" if line.startswith("BOLNA_AGENT_ID=") else line)

print(f"Agent created. BOLNA_AGENT_ID={agent_id} written to .env")
