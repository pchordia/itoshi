## 🔐 Security & Distribution Guide

## Current Security Status

### ❌ NOT Secure for Sharing:
- `.env` file contains plain-text API keys
- Anyone with access to your `.env` can use your API keys
- **DO NOT commit `.env` to git or share it**

### ✅ Now Secure:
- New `secure_config.py` stores keys in **macOS Keychain**
- GUI app checks for keys and prompts user to configure
- Keys never stored in plain text
- Each user sets up their own keys

---

## 🎯 Distribution Options

### Option 1: Share Code (Users Provide Their Own API Keys)

**Best for:** Open source, community projects, developers

**Steps:**

1. **Remove sensitive files from repository:**
```bash
# Make sure .env is in .gitignore
echo ".env" >> .gitignore
echo "logs/" >> .gitignore
echo "outputs/" >> .gitignore
echo "*.pyc" >> .gitignore
echo "__pycache__/" >> .gitignore

git add .gitignore
git commit -m "Add security to .gitignore"
```

2. **Share repository:**
```bash
# Share via GitHub, GitLab, etc.
git push origin main
```

3. **User setup instructions** (include in README):
```markdown
## Setup for Users

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up API keys: `python src/secure_config.py`
4. Run the app: `./launch_gui.sh`
```

**✅ Secure:** Each user provides their own API keys
**✅ Free:** No infrastructure costs
**❌ Technical:** Users need Python knowledge

---

### Option 2: Cloud-Based Service (Your Keys, Managed Access)

**Best for:** Controlled access, paid service, team use

**Architecture:**
```
User → Web App (Frontend) → Your Server (Backend) → APIs
                              ↓
                         Your API Keys
                         (secure server)
```

**Steps:**

1. **Create a backend API server** (Flask/FastAPI):
```python
# api_server.py
from flask import Flask, request, jsonify
from secure_config import SecureConfig

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_video():
    # Verify user authentication
    if not verify_user_token(request.headers.get('Authorization')):
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Use YOUR API keys from server
    # Run generation process
    # Return result
    pass
```

2. **Add authentication:**
   - User accounts (email/password)
   - API tokens or JWT
   - Usage limits/billing

3. **Deploy to cloud:**
   - AWS, Google Cloud, or Heroku
   - Secure environment variables for keys
   - SSL/HTTPS required

**✅ Secure:** Keys never leave your server
**✅ Control:** Manage who has access
**✅ Monetize:** Can charge for usage
**❌ Cost:** Server hosting costs
**❌ Complex:** Requires backend development

---

### Option 3: Hybrid (Local App + License Keys)

**Best for:** Paid software, controlled distribution

**How it works:**
```
User → Local GUI App → License Server → Validation
              ↓
        User provides their own API keys
        (stored in their Keychain)
```

**Steps:**

1. **Create license validation:**
```python
# license_validator.py
def validate_license(license_key: str) -> bool:
    # Check with your license server
    response = requests.post('https://yourlicenseserver.com/validate', 
                            json={'key': license_key})
    return response.json()['valid']
```

2. **Add to GUI app:**
```python
# gui_app.py
class AnimeVideoGeneratorApp:
    def __init__(self, root):
        if not self._validate_license():
            return
        # ... rest of init
```

3. **Distribute app:**
   - Build with py2app
   - Distribute .app bundle
   - Users buy license key from you
   - Users provide their own API keys

**✅ Secure:** API keys belong to each user
**✅ Monetize:** Sell license keys
**✅ Simple:** Users still run locally
**❌ Piracy Risk:** License keys can be shared

---

### Option 4: Enterprise/Team Distribution

**Best for:** Company teams, managed environments

**Setup:**

1. **Create team Keychain:**
```bash
# Create shared keychain accessible to team
security create-keychain -p "team-password" team.keychain
```

2. **Store team API keys:**
```bash
python src/secure_config.py  # Run as admin
# Store keys in team keychain
```

3. **Deploy to team computers:**
   - MDM (Mobile Device Management)
   - Share .app bundle
   - Keychain synced via company infrastructure

**✅ Secure:** Centrally managed keys
**✅ Control:** IT department manages access
**✅ Scalable:** Easy to add/remove users
**❌ Infrastructure:** Requires MDM/IT setup

---

## 🎁 Recommended Approach for Distribution

### For Friends/Testers (Free):
```markdown
1. Share the code repository
2. They run: python src/secure_config.py
3. They provide their own API keys
4. Launch with: ./launch_gui.sh
```

### For Paid Product:
```markdown
1. Build with py2app
2. Add license validation
3. Users buy license + provide own API keys
4. Distribute via website/download link
```

### For SaaS/Web Service:
```markdown
1. Build web frontend (React/Next.js)
2. Build backend API (FastAPI/Flask)
3. Store YOUR API keys on server (secure)
4. User authentication + billing
5. Deploy to cloud provider
```

---

## 🔒 Current Implementation

The app now uses **macOS Keychain** for secure storage:

✅ **First-time user experience:**
1. User downloads/receives the app
2. Runs `python src/secure_config.py`
3. Enters their API keys (stored securely in Keychain)
4. Launches GUI app
5. Keys automatically loaded from Keychain

✅ **Security features:**
- Keys stored in macOS Keychain (encrypted)
- Fallback to .env for development
- GUI prompts if keys missing
- Each user manages their own keys

✅ **What you can safely share:**
- All Python source code
- GUI app
- setup_gui.py for building .app
- Requirements.txt
- Documentation

❌ **Never share:**
- Your `.env` file
- Your API keys
- Log files with conversations
- Generated outputs with user data

---

## 📦 Building for Distribution

### Create .app bundle WITHOUT keys:
```bash
# Build the app
python setup_gui.py py2app

# The built app will prompt users to set up their own keys
# Distribute: dist/AnimeVideoGenerator.app
```

### Share via:
- **Download link:** Upload .zip to Google Drive, Dropbox
- **GitHub Release:** Tag and upload .app as release asset
- **TestFlight (if iOS port):** Apple's official distribution
- **Website:** Host on your own site with download button

---

## 💡 Best Practices

1. **Always** add `.env` to `.gitignore`
2. **Never** hardcode API keys in source code
3. **Use** environment variables or secure storage
4. **Document** setup process for new users
5. **Consider** rate limiting if sharing your keys
6. **Monitor** API usage for unexpected spikes
7. **Rotate** keys if compromised

---

## 🆘 If Your Keys Are Compromised

1. **Immediately revoke** old keys on provider websites:
   - OpenAI: https://platform.openai.com/api-keys
   - Google: https://console.cloud.google.com/apis/credentials
   - Kling: Your Kling account settings

2. **Generate new keys**

3. **Update** secure storage:
```bash
python src/secure_config.py  # Re-run setup with new keys
```

4. **Check usage logs** for unauthorized activity

5. **Report** to provider if fraud detected

