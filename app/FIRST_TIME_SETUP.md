# 🚀 First-Time Setup Guide

## For New Users

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure API Keys (Secure)
```bash
python src/secure_config.py
```

This will prompt you to enter your API keys. They will be stored securely in macOS Keychain (encrypted), never in plain text files.

**You'll need:**
- **OpenAI API Key** (for GPT-5 and image generation)
  - Get it from: https://platform.openai.com/api-keys
- **Google API Key** (for Veo 3 video generation - optional)
  - Get it from: https://console.cloud.google.com/apis/credentials
- **Kling API Keys** (Access Key + Secret Key)
  - Get them from: https://klingai.com (your account settings)

### Step 3: Launch the App
```bash
./launch_gui.sh
```

Or simply:
```bash
python src/gui_app.py
```

---

## 🔐 Where Are My Keys Stored?

Your API keys are stored in **macOS Keychain** - the same secure system that stores your passwords, credit cards, and certificates.

To view them:
1. Open **Keychain Access** app (in /Applications/Utilities)
2. Search for "AnimeVideoGenerator"
3. Your keys are there, encrypted

---

## 🆕 For Developers (Alternative: .env file)

If you prefer using a `.env` file during development:

1. Copy the template:
```bash
cp env_template.txt .env
```

2. Edit `.env` and add your keys:
```bash
nano .env
```

3. **NEVER commit .env to git** (it's already in .gitignore)

The app will automatically fall back to .env if keys aren't in Keychain.

---

## ✅ Verify Setup

After setup, test the app:

1. Launch the GUI: `./launch_gui.sh`
2. If you see the main interface, setup is complete! ✅
3. If you see "API Keys Required" dialog, re-run step 2

---

## 🆘 Troubleshooting

### "Command not found: python"
Try:
```bash
python3 src/secure_config.py
python3 src/gui_app.py
```

### "ModuleNotFoundError"
Make sure you installed dependencies:
```bash
pip install -r requirements.txt
# Or if using pip3:
pip3 install -r requirements.txt
```

### "API Keys Required" dialog keeps appearing
Run the secure config setup again:
```bash
python src/secure_config.py
```

And make sure you complete the setup for at least the OpenAI key.

### Keys aren't saving to Keychain
Check macOS permissions:
1. System Preferences → Security & Privacy → Privacy
2. Make sure Terminal has access

---

## 🎓 What Happens When I Share This?

**Safe to share:**
- ✅ All source code
- ✅ The compiled .app (if built with py2app)
- ✅ This documentation

**DO NOT share:**
- ❌ Your `.env` file
- ❌ Your API keys
- ❌ Contents of `logs/` folder
- ❌ Your personal generated videos/images

**Each user must:**
1. Get their own API keys from OpenAI, Google, Kling
2. Run `python src/secure_config.py` to set up
3. Their keys are stored in THEIR Keychain (not yours)

This way, each person uses their own API credits and keys stay secure! 🔒

