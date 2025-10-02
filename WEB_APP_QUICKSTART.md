# 🚀 Web App Quick Start

## Install & Run (3 steps)

### 1. Install Flask
```bash
pip install flask
```

### 2. Make sure your `.env` file has API keys
```bash
OPENAI_API_KEY=sk-...
KLING_ACCESS_KEY=...
KLING_SECRET_KEY=...
```

### 3. Start the server
```bash
./start_web_app.sh
```

Or directly:
```bash
python web_app.py
```

Then open: **http://localhost:5000**

---

## What It Does

This web app replicates `end_to_end_test.py` but with:
- ✅ User can **upload their own selfie** (drag & drop)
- ✅ Beautiful web UI instead of terminal
- ✅ Real-time progress updates
- ✅ View results directly in browser

## How It Works

1. **Upload selfie** → Drag & drop or click
2. **Chat with GPT-5** → Describe what you want (e.g., "dance", "play guitar")
3. **AI generates prompts** → Custom i2i and i2v prompts
4. **Generate video** → Click button, watch progress
5. **View results** → Anime image + video appear on page

## Files Created

```
web_app.py              ← Flask server (main)
templates/index.html    ← Web page
static/style.css        ← Styling
static/app.js           ← Frontend logic
```

## Port Already Used?

Edit `web_app.py` line 358:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change 5000 → 5001
```

## See Full Documentation

Read `WEB_APP_README.md` for:
- Architecture details
- API endpoints
- Customization options
- Production deployment
- Troubleshooting

---

**That's it! Enjoy! 🎉**

