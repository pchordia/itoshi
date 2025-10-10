# 🚀 Simple Deployment Options (No AWS Needed!)

Much easier alternatives to AWS with simple setup and better pricing.

---

## 🏆 Best Option: Railway.app (Recommended!)

**Why Railway?**
- ✅ Deploy in 5 minutes from GitHub
- ✅ Automatic HTTPS
- ✅ Easy custom domain setup
- ✅ $5/month starter (includes $5 credit)
- ✅ No server management
- ✅ Built-in monitoring

### Setup Railway (10 minutes total)

#### Step 1: Push Code to GitHub (3 min)

```bash
cd /Users/paragchordia/Documents/code/itoshi

# Initialize git if not already
git init
git add .
git commit -m "Initial commit"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/itoshi.git
git push -u origin main
```

#### Step 2: Create Railway Account (2 min)

1. Go to https://railway.app
2. Sign up with GitHub (free)
3. Verify email

#### Step 3: Deploy (5 min)

1. **New Project** → **Deploy from GitHub repo**
2. Select your `itoshi` repo
3. Railway auto-detects it's a Python app!

4. **Add Environment Variables:**
   - Click on your service → **Variables** tab
   - Add:
     ```
     OPENAI_API_KEY=sk-...
     KLING_ACCESS_KEY=...
     KLING_SECRET_KEY=...
     KLING_BASE_URL=https://app.klingai.com
     ANIME_MAX_WORKERS=10
     I2V_MAX_WORKERS=2
     PORT=5001
     ```

5. **Generate Domain:**
   - Click **Settings** → **Generate Domain**
   - You get: `your-app.up.railway.app`

6. **Add Custom Domain:**
   - Click **Settings** → **Custom Domain**
   - Enter: `app.itoshi.ai`
   - Copy the CNAME record shown
   - Go to GoDaddy DNS, add CNAME:
     - Type: **CNAME**
     - Name: **app**
     - Value: **[Railway's CNAME from above]**
   - Wait 5 minutes, Railway auto-configures HTTPS!

**Done!** Visit `https://app.itoshi.ai`

**Cost:** $5/month (includes $5 credit, so essentially free to start)

---

## Option 2: Render.com (Also Very Easy!)

**Why Render?**
- ✅ Free tier available
- ✅ Auto-deploy from GitHub
- ✅ Automatic HTTPS
- ✅ Easy to use

### Setup Render (10 minutes)

#### Step 1: Push to GitHub (if not done)

```bash
cd /Users/paragchordia/Documents/code/itoshi
git init && git add . && git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/itoshi.git
git push -u origin main
```

#### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up with GitHub
3. Verify email

#### Step 3: Create Web Service

1. **New** → **Web Service**
2. Connect your GitHub repo
3. Configure:
   - **Name**: `itoshi-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 300 web_app:app`
   - **Plan**: Starter ($7/month) or Free (spins down after inactivity)

#### Step 4: Add Environment Variables

In **Environment** tab, add:
```
OPENAI_API_KEY=sk-...
KLING_ACCESS_KEY=...
KLING_SECRET_KEY=...
KLING_BASE_URL=https://app.klingai.com
ANIME_MAX_WORKERS=10
I2V_MAX_WORKERS=2
```

#### Step 5: Custom Domain

1. **Settings** → **Custom Domain**
2. Enter: `app.itoshi.ai`
3. Add CNAME in GoDaddy:
   - Name: **app**
   - Value: **[Render's CNAME]**

**Cost:** $7/month (Starter) or Free (with limitations)

---

## Option 3: Fly.io (Global Edge Network)

**Why Fly?**
- ✅ Free tier (3 shared VMs)
- ✅ Global distribution
- ✅ Simple CLI deployment

### Setup Fly.io (15 minutes)

#### Step 1: Install Fly CLI

```bash
# Mac
brew install flyctl

# Or with curl
curl -L https://fly.io/install.sh | sh
```

#### Step 2: Sign Up & Login

```bash
flyctl auth signup
# Or if you have an account:
flyctl auth login
```

#### Step 3: Prepare App

Create `fly.toml`:
```bash
cd /Users/paragchordia/Documents/code/itoshi
flyctl launch
```

Answer prompts:
- App name: `itoshi-app`
- Region: Choose closest to you
- PostgreSQL: No
- Redis: No

This creates `fly.toml`. Edit it:

```toml
app = "itoshi-app"
primary_region = "sjc"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  memory = "2gb"
  cpu_kind = "shared"
  cpus = 2
```

#### Step 4: Set Secrets

```bash
flyctl secrets set \
  OPENAI_API_KEY=sk-... \
  KLING_ACCESS_KEY=... \
  KLING_SECRET_KEY=... \
  KLING_BASE_URL=https://app.klingai.com
```

#### Step 5: Deploy

```bash
flyctl deploy
```

#### Step 6: Custom Domain

```bash
flyctl certs create app.itoshi.ai
```

Add to GoDaddy:
- Type: **A Record**
- Name: **app**
- Value: **[IP shown by Fly]**

**Cost:** Free tier (3 shared VMs) or $5+/month for dedicated

---

## Option 4: Heroku (Classic, Easy)

**Why Heroku?**
- ✅ Very mature platform
- ✅ Simple git-based deployment
- ✅ Lots of add-ons

### Setup Heroku (10 minutes)

#### Step 1: Install Heroku CLI

```bash
brew tap heroku/brew && brew install heroku
```

#### Step 2: Login & Create App

```bash
heroku login
heroku create itoshi-app
```

#### Step 3: Add Python Buildpack

```bash
heroku buildpacks:set heroku/python
```

#### Step 4: Set Environment Variables

```bash
heroku config:set OPENAI_API_KEY=sk-...
heroku config:set KLING_ACCESS_KEY=...
heroku config:set KLING_SECRET_KEY=...
heroku config:set KLING_BASE_URL=https://app.klingai.com
```

#### Step 5: Create Procfile

```bash
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT --timeout 300 web_app:app" > Procfile
git add Procfile
git commit -m "Add Procfile"
```

#### Step 6: Deploy

```bash
git push heroku main
```

#### Step 7: Custom Domain

```bash
heroku domains:add app.itoshi.ai
```

Add to GoDaddy:
- Type: **CNAME**
- Name: **app**
- Value: **[DNS target from Heroku]**

**Cost:** $7-25/month (Eco/Basic/Standard dynos)

---

## Option 5: DigitalOcean App Platform

**Why DigitalOcean?**
- ✅ Simple UI
- ✅ Good documentation
- ✅ Reasonable pricing

### Setup DigitalOcean (10 minutes)

1. Go to https://digitalocean.com
2. **Create** → **Apps**
3. Connect GitHub repo
4. Configure:
   - **Name**: itoshi-app
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `gunicorn -w 4 -b 0.0.0.0:8080 --timeout 300 web_app:app`
   - **HTTP Port**: 8080

5. Add environment variables in **Environment Variables** section

6. Choose plan: Basic ($5/month)

7. **Settings** → **Domains** → Add `app.itoshi.ai`
   - Add CNAME in GoDaddy to DO's value

**Cost:** $5-12/month

---

## 🎯 Quick Comparison

| Platform | Setup Time | Cost/Month | Free Tier | Custom Domain | Auto HTTPS |
|----------|------------|------------|-----------|---------------|------------|
| **Railway** ⭐ | 10 min | $5+ | $5 credit | ✅ Easy | ✅ Auto |
| **Render** | 10 min | $7+ | ✅ Limited | ✅ Easy | ✅ Auto |
| **Fly.io** | 15 min | Free-$5+ | ✅ Yes | ✅ Easy | ✅ Auto |
| **Heroku** | 10 min | $7+ | ❌ No | ✅ Easy | ✅ Auto |
| **DigitalOcean** | 10 min | $5+ | ❌ No | ✅ Easy | ✅ Auto |
| AWS EC2 | 30 min | $42+ | ⚠️ Complex | ⚠️ Manual | ⚠️ Manual |

---

## 🏆 My Recommendation for You: Railway

**Railway.app is the easiest:**

1. Push code to GitHub (5 min)
2. Connect Railway to GitHub (1 min)
3. Add environment variables (2 min)
4. Add custom domain CNAME (2 min)
5. **Done!**

**Total time: 10 minutes**
**Total cost: $5/month** (includes $5 credit free trial)

---

## 🚀 Railway Quick Start Script

I'll create a helper script to make this even easier...

```bash
# 1. Push to GitHub first
cd /Users/paragchordia/Documents/code/itoshi
git init
git add .
git commit -m "Initial commit"
# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/itoshi.git
git push -u origin main

# 2. Go to railway.app
# 3. New Project → Deploy from GitHub repo
# 4. Add environment variables
# 5. Add custom domain: app.itoshi.ai
# 6. Copy CNAME and add to GoDaddy

# Done! 🎉
```

---

## 📝 What You Need

1. **GitHub account** (free) - to store code
2. **Railway/Render/Fly account** (free to start) - to host app
3. **GoDaddy access** (you have) - to point domain
4. **API keys** (you have) - OpenAI, Kling

---

## 🔧 Required File Changes

Create `railway.json` (only if using Railway):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 300 web_app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

No other changes needed! Railway auto-detects Python and requirements.txt.

---

## Need Help?

Railway has excellent docs: https://docs.railway.app/
Render docs: https://render.com/docs
Fly.io docs: https://fly.io/docs/

All three have helpful communities and fast support!

