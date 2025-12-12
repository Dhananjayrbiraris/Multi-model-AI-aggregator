# Multi-model-AI-aggregator

A production‑grade **Streamlit UI + n8n Orchestration** system that allows users to:

- Run **single model** AI inference
- Run **multiple models in parallel**
- Support **text, image, and audio inputs**
- Display latency + per‑model responses in a clean UI

This project integrates:
- **2 Large Language Models:** GPT‑4o, GPT‑4o‑mini
- **2 Multimodal Models:** Whisper (audio → text), GPT‑4o Vision (image analysis)

---

## 🚀 Features

### ✅ Streamlit Frontend
- Select models (LLM + multimodal)
- Choose input type (text / image / audio)
- Upload files (image/audio)
- Enter text prompt
- Clean and modern dark UI
- Hidden webhook URL (secured via environment variable)
- Response cards with model name + latency

### ✅ n8n Backend Orchestrator
- Webhook endpoint for receiving UI requests
- Extracts prompt, models, and input type
- Splits model array into **parallel execution branches**
- Routes requests dynamically using Switch Router
- Executes OpenAI models
- Formats each model output
- Aggregates everything into a final JSON array
- Returns response back to Streamlit

---

## 🏗️ System Architecture
```
Streamlit UI → API Layer (Webhook POST) → n8n Orchestration
         → Split Models → Route → Execute Models in Parallel
         → Format → Aggregate → Respond → UI Results Panel
```

### Components
- **API Layer:** Streamlit → n8n webhook
- **Orchestration Layer:** request extraction, model routing, parallel execution
- **Model Adapters:** GPT‑4o, GPT‑4o‑mini, Whisper, GPT‑4o Vision
- **Storage (optional):** Redis for caching
- **Logging:** n8n execution logs + Streamlit console logs

---

## 🔄 Request Flow

### **Single Model Mode**
```
UI → Webhook → Extract Request → Route Model → Execute → Format → Aggregate → UI
```

### **Multi‑Model Parallel Mode**
```
UI → Webhook → Extract Request → Split Models
    → Branch A (GPT‑4o)
    → Branch B (GPT‑4o‑mini)
    → Branch C (Whisper)
    → Branch D (Vision)
All branches → Format → Aggregate → UI
```

---

## 📦 Project Structure
```
/streamlit-app
│── app.py                   # Frontend UI
│── assets/                  # Uploaded files (optional)

/n8n-workflow
│── Multi-Model Aggregator.json  # Full workflow export

/docs
│── System_Architecture_Document.docx
```

---

## ⚙️ Setup Instructions

### **1. Install dependencies**
```bash
pip install streamlit requests python-dotenv
```

### **2. SetWebhook URL (Secure)**
In your terminal:
```bash
export N8N_WEBHOOK_URL="https://your-domain.app.n8n.cloud/webhook/multi"
```
Windows (PowerShell):
```powershell
setx N8N_WEBHOOK_URL "https://your-domain.app.n8n.cloud/webhook/multi"
```

### **3. Run Streamlit App**
```bash
streamlit run app.py
```

---

## 🧠 Models Supported
| Model | Type | Purpose |
|-------|-------|---------|
| GPT‑4o | LLM | General reasoning, text generation |
| GPT‑4o‑mini | LLM | Fast, lightweight responses |
| Whisper | Audio → Text | Speech transcription |
| GPT‑4o Vision | Image → Text | Image understanding |

---

## 📈 Scaling Strategy
- Streamlit is stateless → horizontally scalable
- n8n workflows can run in distributed mode
- Parallel execution built‑in via Split node
- Add Redis for prompt caching
- Add RabbitMQ for long‑running multimodal jobs

---

## 🔐 User Management Strategy
- Add JWT / API keys for authentication
- Per‑user model access rules
- Rate-limiting via n8n Rate Limit node
- Logging & usage analytics via Postgres + n8n

---

## 🛡️ Uptime & Monitoring
- n8n execution logs for debugging
- Prometheus + Grafana integration
- Auto‑restart workflows on failure
- Graceful degradation: failed model doesn't block others

---

## 📬 Output Example
```json
{
  "responses": [
    { "model": "gpt4o", "response": "Hello!", "latencyMs": 1240 },
    { "model": "whisper", "response": "Transcribed text...", "latencyMs": 1790 }
  ]
}
```

---

## 🤝 Contribution
Feel free to fork and enhance this multi‑model inference orchestrator.

---


## 💬 Need help?
Just ask — happy to help you extend this architecture further!
