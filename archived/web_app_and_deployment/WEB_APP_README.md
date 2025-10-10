# 🎬 Interactive Anime Video Generator - Web App

A beautiful web application that turns your selfies into anime characters doing anything you imagine!

## ✨ Features

1. **📸 Photo Upload** - Drag & drop or click to upload your selfie
2. **💬 Interactive AI Chat** - GPT-5 asks clarifying questions to understand your vision
3. **🎨 Custom Prompt Generation** - Automatically generates tailored i2i and i2v prompts
4. **🎬 Video Generation** - Creates anime image + animated video using OpenAI and Kling AI
5. **📊 Real-time Progress** - Live updates as your video is being generated

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Make sure your `.env` file has the required API keys:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key
KLING_ACCESS_KEY=your_kling_access_key
KLING_SECRET_KEY=your_kling_secret_key

# Optional (uses defaults if not set)
ANALYSIS_MODEL=chatgpt-5
```

### 3. Run the Web App

```bash
python web_app.py
```

The server will start on `http://localhost:5000`

Open your browser and navigate to that URL!

## 📖 How to Use

### Step 1: Upload Your Selfie
- Click the upload area or drag & drop an image
- Supports PNG, JPG, WEBP (max 16MB)

### Step 2: Describe What You Want
- Example: "dance", "eat ramen", "play basketball"
- GPT-5 will ask clarifying questions (up to 5)
- Answer naturally in the chat interface

### Step 3: Review Generated Prompts
- See the custom i2i (image) and i2v (video) prompts
- These are tailored specifically to your request

### Step 4: Generate Your Video
- Click "Generate Video"
- Watch real-time progress logs
- i2i generation takes ~1-2 minutes
- i2v generation takes ~1-2 minutes

### Step 5: Enjoy Your Results!
- View your anime image and video
- Click "Create Another" to start fresh

## 🏗️ Architecture

### Backend (Flask)
- **`web_app.py`** - Main Flask server with API endpoints
- **`src/interactive_prompt_builder.py`** - GPT-5 conversation manager
- **`src/batch_media.py`** - Core i2i and i2v processing

### Frontend
- **`templates/index.html`** - Single-page application
- **`static/style.css`** - Modern dark theme with gradients
- **`static/app.js`** - Interactive UI with real-time updates

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve main page |
| `/api/start` | POST | Start conversation with GPT-5 |
| `/api/message` | POST | Send message in conversation |
| `/api/upload` | POST | Upload selfie image |
| `/api/generate` | POST | Start i2i + i2v generation |
| `/api/status` | GET | Poll generation status |
| `/api/reset` | POST | Reset session |
| `/outputs/<path>` | GET | Serve generated files |

## 📁 File Structure

```
itoshi/
├── web_app.py              # Flask web server
├── templates/
│   └── index.html          # Main HTML page
├── static/
│   ├── style.css           # Styles
│   └── app.js              # Frontend logic
├── src/
│   ├── batch_media.py      # Core processing
│   ├── interactive_prompt_builder.py
│   └── secure_config.py
├── prompts/
│   ├── image_prompt_interactive.txt
│   └── video_prompt_interactive.txt
├── uploads/                # User uploads (auto-created)
└── outputs/
    └── web/                # Generated files (auto-created)
```

## 🔧 Configuration

### Environment Variables

All configuration is in `.env`:

```bash
# API Keys
OPENAI_API_KEY=...
KLING_ACCESS_KEY=...
KLING_SECRET_KEY=...

# Model Selection
ANALYSIS_MODEL=chatgpt-5          # For GPT-5 conversations

# Generation Settings
IMAGE_SIZE=auto                   # i2i image size
VIDEO_DURATION_SECONDS=5          # i2v video length
KLING_MODEL=Professional v2.1     # Kling model

# Worker/Timeout Settings
ANIME_MAX_WORKERS=20
I2V_MAX_WORKERS=3
REQUEST_TIMEOUT_SECONDS=120
MAX_RETRIES=6
```

### Flask Settings

In `web_app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs/web'
```

## 🎨 Customization

### Change Theme Colors

Edit `static/style.css`:

```css
:root {
    --primary-color: #6366f1;    /* Indigo */
    --secondary-color: #8b5cf6;  /* Purple */
    --bg-color: #0f172a;         /* Dark blue */
    /* ... */
}
```

### Adjust Question Limit

In `web_app.py`:

```python
self.builder = InteractivePromptBuilder(max_questions=5)  # Change here
```

### Change Polling Interval

In `static/app.js`:

```javascript
}, 2000); // Poll every 2 seconds (change here)
```

## 🚨 Troubleshooting

### Port Already in Use

```bash
# Change port in web_app.py
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Large File Upload Fails

Increase max size in `web_app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
```

### Generation Stuck

Check the terminal running `web_app.py` for errors. The generation runs in a background thread and logs to console.

### Session Lost

Browser sessions expire after inactivity. Click "Create Another" or refresh the page.

## 🔒 Security Notes

- Sessions use Flask's built-in session management
- File uploads are validated for type and size
- Filenames are sanitized with `secure_filename()`
- Each user session has isolated upload/output directories
- Temporary files are cleaned up after generation

## 📝 Production Deployment

For production, use a proper WSGI server:

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
```

Or with nginx as reverse proxy:

```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**Important for Production:**
- Set `app.debug = False`
- Use proper secret key (not `os.urandom(24)`)
- Enable HTTPS
- Add rate limiting
- Add authentication if needed
- Set up proper logging
- Configure CORS if needed

## 💡 Tips

1. **Best selfie photos**: Clear face, good lighting, neutral background
2. **Good descriptions**: Be specific! "dance salsa" > "dance"
3. **Answer questions**: More details = better results
4. **Be patient**: Total generation takes 2-4 minutes
5. **Try different styles**: Each generation is unique!

## 🆚 Differences from CLI

| Feature | CLI (`batch_media.py`) | Web App |
|---------|------------------------|---------|
| Interface | Command line | Web browser |
| Prompts | Pre-defined in files | Generated by GPT-5 |
| Batch processing | ✅ Multiple images | ❌ One at a time |
| Photo upload | Folder on disk | Drag & drop |
| Real-time updates | Terminal output | Live web UI |
| Session management | ❌ | ✅ |

## 🔗 Related Files

- **Command-line version**: `src/batch_media.py`
- **End-to-end test**: `src/end_to_end_test.py` (CLI interactive)
- **Prompt files**: `prompts/anime_prompts.txt`, `prompts/kling_prompts.txt`

## 📄 License

Same as parent project.

---

**Enjoy creating amazing anime videos! 🎉**

