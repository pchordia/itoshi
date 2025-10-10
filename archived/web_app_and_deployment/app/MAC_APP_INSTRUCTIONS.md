# Creating a Standalone Mac App

## Option 1: Simple Launch (Quick Start)

Just double-click `launch_gui.sh` or run:
```bash
./launch_gui.sh
```

## Option 2: Create a Mac .app Bundle (Recommended)

Use **py2app** to create a standalone Mac application:

### Step 1: Install py2app
```bash
pip install py2app
```

### Step 2: Create setup.py
Already created for you at `setup_gui.py`

### Step 3: Build the app
```bash
python setup_gui.py py2app
```

This will create:
- `dist/AnimeVideoGenerator.app` - Your standalone Mac app!

### Step 4: Move to Applications
```bash
mv dist/AnimeVideoGenerator.app /Applications/
```

Now you can launch it like any other Mac app from your Applications folder!

## Option 3: Create a Double-Clickable App (Simple)

### Using Automator (Built into macOS):

1. Open **Automator** (in /Applications/Utilities)
2. Choose **Application**
3. Search for "Run Shell Script" and drag it to the workflow
4. Paste this script:
```bash
cd /Users/paragchordia/Documents/code/itoshi
python3 src/gui_app.py
```
5. Save as "AnimeVideoGenerator" to your Desktop or Applications folder
6. Right-click the app → Get Info → change icon if desired

## Features of the GUI App

✨ **Interactive GUI** with:
- 📁 File picker for selecting selfie images
- 💬 Real-time conversation with GPT-5
- ⏱️ Response time tracking
- 🎨 Automatic i2i generation (OpenAI gpt-image)
- 🎬 Automatic i2v generation (Kling)
- 📊 Progress status updates
- 🔄 "Create another video" workflow

## Requirements

- Python 3.10+
- All dependencies from `requirements.txt`
- `.env` file configured with API keys
- macOS (tested on macOS 10.14+)

## GUI Layout

```
┌─────────────────────────────────────────┐
│  🎬 Interactive Anime Video Generator   │
├─────────────────────────────────────────┤
│  Step 1: Select Your Selfie             │
│  [No image selected]  [Choose Image...] │
├─────────────────────────────────────────┤
│  Step 2: What do you want to do?        │
│  [eat ramen____________] [Start →]      │
├─────────────────────────────────────────┤
│  Step 3: Interactive Q&A (GPT-5)        │
│  ┌───────────────────────────────────┐  │
│  │ Conversation history shows here   │  │
│  │ with color-coded messages         │  │
│  └───────────────────────────────────┘  │
│  [Type your answer here...] [Send]      │
├─────────────────────────────────────────┤
│  Step 4: Generate Video                 │
│  [🎬 Generate Anime Video]              │
├─────────────────────────────────────────┤
│  Status: Ready                          │
└─────────────────────────────────────────┘
```

## Troubleshooting

### App won't open
- Check that all Python dependencies are installed
- Verify `.env` file exists with API keys
- Try running from terminal first: `./launch_gui.sh`

### "App from unidentified developer"
- Right-click app → Open (instead of double-clicking)
- Or go to System Preferences → Security & Privacy → allow the app

### Performance issues
- GPT-5 responses may take 2-5 seconds
- i2i generation takes 30-60 seconds
- i2v generation takes 2-3 minutes
- All processing happens in background threads (UI stays responsive)

