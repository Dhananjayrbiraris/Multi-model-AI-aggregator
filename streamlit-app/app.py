# app.py — Streamlit UI (Sidebar) | Clean, Stable, No Webhook in UI
# Webhook is NOT shown in UI. Set environment variable:
#   export N8N_WEBHOOK_URL="https://your-n8n-webhook.url"

import os
import json
import time
import base64
from typing import List, Dict, Any

import requests
import streamlit as st

# -------------------------------------------------
# Hidden configuration (Option A)
# -------------------------------------------------
WEBHOOK_URL = os.environ.get(
    "N8N_WEBHOOK_URL",
     "https://sp12012012.app.n8n.cloud/webhook-test/multi"  # fallback if env var not set
)

AVAILABLE_MODELS = [
    {"id": "gpt4o", "title": "GPT-4o", "desc": "High-capacity LLM"},
    {"id": "gpt4o-mini", "title": "GPT-4o Mini", "desc": "Faster, cheaper LLM"},
    {"id": "whisper", "title": "Whisper", "desc": "Audio → text transcription"},
    {"id": "gpt4o-vision", "title": "Vision", "desc": "Image understanding"},
]

# -------------------------------------------------
# Streamlit Page Setup
# -------------------------------------------------
st.set_page_config(
    page_title="n8n Multi Model UI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(
    """
    <style>
    .stApp { background: #0b0f12; color: #e6eef6; font-family: Inter, sans-serif; }
    .header-card {
        background: rgba(255,255,255,0.02);
        border-radius: 12px; padding: 18px;
        border:1px solid rgba(255,255,255,0.06);
    }
    .avatar { width:35px;height:35px;border-radius:8px;
              background:linear-gradient(90deg,#fb923c,#ef4444);margin-right:12px; }
    .muted { color:#9fb0c8;font-size:13px; }
    .results-card { background:#071018;border-radius:10px;padding:14px;
                    border:1px solid rgba(255,255,255,0.05); }
    .resp-card { background:rgba(255,255,255,0.02);border-radius:8px;
                 padding:10px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.04); }
    .resp-title { font-weight:700;color:#e6eef6;font-size:15px; }
    .resp-lat { color:#93aec6;font-size:12px; }
    .stTextArea textarea {
        background:#061018 !important;
        border:1px solid rgba(255,255,255,0.04) !important;
        color:white !important;
        border-radius:8px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Sidebar UI
# -------------------------------------------------
st.sidebar.markdown(
    "<div style='display:flex;align-items:center;'>"
    "<div class='avatar'></div>"
    "<div><b style='font-size:16px;'>n8n Multi — Controls</b>"
    "<div class='muted'>Select models & input.</div></div></div>",
    unsafe_allow_html=True
)
st.sidebar.markdown("---")

# Model selection
selected_models = []
for m in AVAILABLE_MODELS:
    key = f"mdl_{m['id']}"
    default = True if m["id"] == "gpt4o" else False
    if st.sidebar.checkbox(f"{m['title']} — {m['desc']}", value=default, key=key):
        selected_models.append(m["id"])

if not selected_models:
    st.sidebar.warning("At least one model required — GPT-4o enabled.")
    selected_models = ["gpt4o"]

st.sidebar.markdown("---")

input_type = st.sidebar.radio("Input Type", ["text", "image", "audio"])
prompt_text = st.sidebar.text_area("Prompt (Optional)", height=120)

uploaded_file = None
if input_type in ("image", "audio"):
    uploaded_file = st.sidebar.file_uploader(f"Upload {input_type} file")

st.sidebar.markdown("---")
run = st.sidebar.button("🚀 Run Models", use_container_width=True)

# -------------------------------------------------
# Main Body Header
# -------------------------------------------------
st.markdown(
    """
    <div class='header-card'>
        <div style='display:flex;align-items:center;'>
            <div class='avatar'></div>
            <div>
                <div style='font-size:20px;font-weight:700;'>n8n Multi-Model Client</div>
                <div class='muted'>Your clean UI for multi-model tasks.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

left, right = st.columns([1, 2])

with left:
    st.markdown("### Request Summary")
    st.write(f"**Models:** {', '.join(selected_models)}")
    st.write(f"**Input type:** {input_type}")
    if prompt_text:
        st.write(f"**Prompt:** {prompt_text[:120]}…")
    if uploaded_file and input_type == "image":
        st.image(uploaded_file)
    elif uploaded_file:
        st.write(f"**File:** {uploaded_file.name}")

status_box = right.empty()
results_box = right.empty()

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def image_to_data_url(data: bytes, filename: str) -> str:
    ext = filename.split(".")[-1].lower()
    mime = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/png")

    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"


def send_json(url: str, payload: Dict[str, Any]):
    start = time.time()
    r = requests.post(url, json=payload, timeout=180)
    return r, time.time() - start


def send_multipart(url: str, file_bytes, filename, data: Dict[str, Any]):
    start = time.time()
    r = requests.post(url, files={"file": (filename, file_bytes)}, data=data, timeout=300)
    return r, time.time() - start


# --- FIXED + SAFE normalize_response (no latency errors) ---
def normalize_response(body):
    """
    Always return list of:
    {
        "model": str,
        "response": str,
        "latency": int
    }
    """
    out = []

    # n8n often wraps responses in "responses"
    if isinstance(body, dict) and "responses" in body:
        body = body["responses"]

    # Dictionary response (model → data)
    if isinstance(body, dict):
        for model, val in body.items():
            if isinstance(val, dict):
                response_text = (
                    val.get("response")
                    or val.get("text")
                    or json.dumps(val, indent=2)
                )
                latency = (
                    val.get("latency")
                    or val.get("latencyMs")
                    or val.get("latency_ms")
                    or 0
                )
            else:
                response_text = str(val)
                latency = 0

            out.append({
                "model": model,
                "response": response_text,
                "latency": latency
            })
        return out

    # List of items
    if isinstance(body, list):
        for item in body:
            if isinstance(item, dict):
                out.append({
                    "model": item.get("model", "unknown"),
                    "response": item.get("response") or item.get("text") or json.dumps(item, indent=2),
                    "latency": item.get("latency") or item.get("latencyMs") or item.get("latency_ms") or 0
                })
            else:
                out.append({
                    "model": "result",
                    "response": str(item),
                    "latency": 0
                })
        return out

    # Fallback simple value
    return [{
        "model": "result",
        "response": str(body),
        "latency": 0
    }]


# -------------------------------------------------
# RUN BUTTON HANDLER
# -------------------------------------------------
if run:
    if not WEBHOOK_URL:
        st.error("Webhook is not configured. Set N8N_WEBHOOK_URL.")
        st.stop()

    status_box.info("⏳ Sending request...")

    try:
        # ---- TEXT ----
        if input_type == "text":
            payload = {
                "prompt": prompt_text,
                "models": selected_models,
                "inputType": "text"
            }
            resp, elapsed = send_json(WEBHOOK_URL, payload)

        # ---- AUDIO ----
        elif input_type == "audio":
            if not uploaded_file:
                st.warning("Upload an audio file.")
                st.stop()

            data = {
                "models": json.dumps(selected_models),
                "inputType": "audio",
                "prompt_text": prompt_text
            }
            resp, elapsed = send_multipart(WEBHOOK_URL, uploaded_file.read(), uploaded_file.name, data)

        # ---- IMAGE ----
        elif input_type == "image":
            if not uploaded_file:
                st.warning("Upload an image.")
                st.stop()

            raw = uploaded_file.read()
            data_url = image_to_data_url(raw, uploaded_file.name)

            data = {
                "models": json.dumps(selected_models),
                "inputType": "image",
                "prompt_text": prompt_text,
                "data_url": data_url
            }

            resp, elapsed = send_multipart(WEBHOOK_URL, raw, uploaded_file.name, data)

        # ---- RESPONSE HANDLER ----
        if resp.status_code >= 200 and resp.status_code < 300:
            try:
                body = resp.json()
            except:
                body = {"raw": resp.text}

            items = normalize_response(body)
            status_box.success(f"✅ Success — {elapsed:.2f}s")

            with results_box:
                st.markdown("### Results")

                for item in items:
                    st.markdown(
                        f"""
                        <div class='resp-card'>
                            <div class='resp-title'>{item['model']}</div>
                            <div class='resp-lat'>Latency: {item['latency']} ms</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.code(item["response"])

        else:
            status_box.error(f"❌ Error {resp.status_code}")
            results_box.write(resp.text)

    except Exception as e:
        status_box.error("❌ Request failed")
        results_box.write(str(e))
