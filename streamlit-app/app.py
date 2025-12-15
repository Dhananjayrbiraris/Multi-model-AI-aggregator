# -------------------------------------------------
# app.py — Clean Streamlit UI (Binary File Transfer)
# -------------------------------------------------

import os
import json
import time
from typing import Dict, Any, Optional

import requests
import streamlit as st

# -------------------------------------------------
# Configuration
# -------------------------------------------------
WEBHOOK_URL = os.environ.get(
    "N8N_WEBHOOK_URL",
    # "https://sp12012012.app.n8n.cloud/webhook/multi",
    "https://sunny045.app.n8n.cloud/webhook/multi"
)

AVAILABLE_MODELS = [
    {"id": "gpt4o", "title": "GPT-4o", "desc": "High-capacity LLM"},
    {"id": "gpt4o-mini", "title": "GPT-4o Mini", "desc": "Fast, cheap LLM"},
    {"id": "whisper", "title": "Whisper", "desc": "Audio → Text"},
    {"id": "gpt4o-vision", "title": "Vision", "desc": "Image understanding"},
]

# -------------------------------------------------
# Streamlit Page Setup
# -------------------------------------------------
st.set_page_config(
    page_title="AI Multi Model UI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# CSS
# -------------------------------------------------
st.markdown("""
<style>
.stApp { background:#0b0f12; color:#e6eef6; font-family:Inter, sans-serif; }
.header-card { background:rgba(255,255,255,0.02); border-radius:12px; padding:18px;
               border:1px solid rgba(255,255,255,0.06); }
.avatar { width:35px; height:35px; border-radius:8px;
          background:linear-gradient(90deg,#fb923c,#ef4444); margin-right:12px; }
.muted { color:#9fb0c8; font-size:13px; }
.resp-card { background:rgba(255,255,255,0.02); border-radius:8px;
             padding:12px; border:1px solid rgba(255,255,255,0.04); margin-bottom:12px; }
.resp-title { font-weight:700; font-size:15px; }
.resp-lat { color:#93aec6; font-size:12px; }
.stTextArea textarea { background:#061018 !important;
                       border:1px solid rgba(255,255,255,0.04) !important;
                       color:white !important; border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.markdown("""
<div style="display:flex;align-items:center;">
<div class='avatar'></div>
<div><b style='font-size:16px;'>AI Multi — Controls</b>
<div class='muted'>Choose models & input.</div></div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

selected_model = st.sidebar.radio(
    "Select Model",
    AVAILABLE_MODELS,
    format_func=lambda m: f"{m['title']} — {m['desc']}"
)

selected_models = [selected_model["id"]]


input_type = st.sidebar.radio("Input Type", ["text", "image", "audio"])
prompt_text = st.sidebar.text_area("Prompt (Optional)", height=120)

uploaded_file = None
uploaded_bytes: Optional[bytes] = None

# 📎 Pin-style attachment (shown only when needed)
if input_type in ("image", "audio"):
    st.markdown("📎 **Attach file**")
    uploaded_file = st.file_uploader(
        "",
        type=["png", "jpg", "jpeg", "wav", "mp3", "m4a"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        uploaded_file.seek(0)
        uploaded_bytes = uploaded_file.read()
        st.caption(f"📎 Attached: {uploaded_file.name}")

# Chat input (unchanged)
user_message = st.chat_input("Type your message…")

# Run trigger (Enter key OR button)
run = bool(user_message)



# -------------------------------------------------
# Header
# -------------------------------------------------
st.markdown("""
<div class='header-card'>
<div style='display:flex;align-items:center;'>
    <div class='avatar'></div>
    <div>
        <div style='font-size:20px;font-weight:700;'>AI Multi-Model Client</div>
        <div class='muted'>Send text, image, or audio to multiple models.</div>
    </div>
</div>
</div>
""", unsafe_allow_html=True)


# -------------------------------------------------
# Helper Functions
# -------------------------------------------------
def send_json(url: str, payload: Dict[str, Any]):
    start = time.time()
    r = requests.post(url, json=payload, timeout=180)
    return r, time.time() - start


def send_binary(url: str, file_bytes: bytes, filename: str, mime_type: str, meta: Dict[str, Any]):
    """
    Sends RAW binary file (no multipart, no base64, no encoding)
    Backend receives:
    - headers: metadata
    - raw request body: binary file
    """
    headers = {
        "Content-Type": mime_type,
        "Filename": filename,
        "Models": json.dumps(meta["models"]),
        "Input-Type": meta["inputType"],
        "Prompt": meta.get("prompt", "")
    }

    start = time.time()
    r = requests.post(url, data=file_bytes, headers=headers, timeout=300)
    return r, time.time() - start


def send_multipart(url, file_bytes, filename, doc: Dict[str, Any], mime=None):
    start = time.time()
    files = {"file": (filename, file_bytes, mime)}
    r = requests.post(url, files=files, data=doc, timeout=300)
    return r, time.time() - start


def normalize_response(body):
    """
    Standard response format:
    [
      {"model": "", "response": "", "latency": ""}
    ]
    """
    out = []

    if isinstance(body, dict) and "responses" in body:
        body = body["responses"]

    if isinstance(body, dict):
        for m, data in body.items():
            txt = (
                data.get("response") or
                data.get("text") or
                json.dumps(data, indent=2)
            )
            lat = (
                data.get("latency") or
                data.get("latencyMs") or
                data.get("latency_ms") or 0
            )
            out.append({"model": m, "response": txt, "latency": lat})
        return out

    if isinstance(body, list):
        for item in body:
            out.append({
                "model": item.get("model", "unknown"),
                "response": item.get("response") or item.get("text") or json.dumps(item),
                "latency": item.get("latency", 0)
            })
        return out

    return [{"model": "unknown", "response": str(body), "latency": 0}]


# -------------------------------------------------
# RUN
# -------------------------------------------------
results_box = st.empty()
status_box = st.empty()

if run:
    if not WEBHOOK_URL:
        st.error("Webhook not configured")
        st.stop()

    status_box.info("⏳ Sending request...")

    try:
        # ---------------- TEXT ----------------
        if input_type == "text":
            payload = {
                "prompt": prompt_text,
                "models": selected_models,
                "inputType": "text"
            }
            resp, elapsed = send_json(WEBHOOK_URL, payload)

        # ---------------- AUDIO (RAW BYTES) ----------------
        elif input_type == "audio":
            if not uploaded_bytes:
                st.warning("Upload an audio file.")
                st.stop()

            resp, elapsed = send_binary(
                WEBHOOK_URL,
                uploaded_bytes,
                uploaded_file.name,
                uploaded_file.type or "application/octet-stream",
                {
                    "models": selected_models,
                    "inputType": "audio",
                    "prompt": prompt_text or ""
                }
            )

        # ---------------- IMAGE (RAW BYTES via multipart) ----------------
        elif input_type == "image":
            if not uploaded_bytes:
                st.warning("Upload an image.")
                st.stop()

            resp, elapsed = send_multipart(
                WEBHOOK_URL,
                uploaded_bytes,
                uploaded_file.name,
                {
                    "models": json.dumps(selected_models),
                    "inputType": "image",
                    "prompt": prompt_text or ""
                },
                mime=uploaded_file.type
            )

        # ---------------- RESPONSE ----------------
        if 200 <= resp.status_code < 300:
            try:
                data = resp.json()
            except:
                data = {"raw": resp.text}

            items = normalize_response(data)
            status_box.success(f"✅ Success — {elapsed:.2f}s")

            with results_box:
                st.markdown("### Results")
                for item in items:
                    st.markdown(f"""
                        <div class='resp-card'>
                            <div class='resp-title'>{item['model']}</div>
                            <div class='resp-lat'>Latency: {item['latency']} ms</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.code(item["response"])

        else:
            status_box.error(f"❌ Error {resp.status_code}")
            results_box.write(resp.text)

    except Exception as e:
        status_box.error("❌ Failed")
        results_box.write(str(e))
