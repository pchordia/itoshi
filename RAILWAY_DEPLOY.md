# 🚂 Railway Deployment - Step by Step

The **easiest** way to deploy app.itoshi.ai in under 10 minutes!

---

## Why Railway?

- ✅ **5 minutes** to deploy
- ✅ **$5/month** (includes $5 free credit to start)
- ✅ **Automatic HTTPS**
- ✅ **No server management**
- ✅ **Auto-deploy** on every git push
- ✅ **Built-in monitoring**

---

## Step 1: Push to GitHub (3 minutes)

### Option A: Use Helper Script

```bash
cd /Users/paragchordia/Documents/code/itoshi
./deploy_to_github.sh
```

The script will:
1. Initialize git if needed
2. Commit your changes
3. Ask for your GitHub repo URL
4. Push everything

### Option B: Manual

```bash
cd /Users/paragchordia/Documents/code/itoshi

# Create repo on GitHub first (https://github.com/new)
# Name it: itoshi-app
# DO NOT initialize with README

# Then run:
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/itoshi-app.git
git push -u origin main
```

---

## Step 2: Create Railway Account (1 minute)

1. Go to https://railway.app
2. Click **"Login"**
3. Choose **"Login with GitHub"**
4. Authorize Railway
5. Verify your email

---

## Step 3: Deploy Your App (2 minutes)

### 3a. Create New Project

1. Click **"New Project"**
2. Choose **"Deploy from GitHub repo"**
3. Select your repository: `itoshi-app`
4. Railway starts building automatically!

### 3b. Wait for Build

Watch the build logs. It will:
- ✅ Detect Python
- ✅ Install dependencies from `requirements.txt`
- ✅ Start with gunicorn (from `railway.json`)
- Takes ~2 minutes

---

## Step 4: Add Environment Variables (2 minutes)

1. Click on your deployed service
2. Click **"Variables"** tab
3. Click **"+ New Variable"**
4. Add each one:

```
OPENAI_API_KEY=sk-proj-...your-key...
KLING_ACCESS_KEY=...your-key...
KLING_SECRET_KEY=...your-key...
KLING_BASE_URL=https://app.klingai.com
ANIME_MAX_WORKERS=10
I2V_MAX_WORKERS=2
ANALYSIS_MODEL=chatgpt-5
```

5. App will auto-restart with new variables

---

## Step 5: Test Your App (1 minute)

1. Click **"Settings"** tab
2. Click **"Generate Domain"**
3. You get: `itoshi-app-production.up.railway.app` (or similar)
4. Click the URL to open it
5. **Test that your app works!** 🎉

---

## Step 6: Add Custom Domain (2 minutes)

### 6a. In Railway

1. Still in **"Settings"** tab
2. Scroll to **"Custom Domain"**
3. Click **"+ Custom Domain"**
4. Enter: `app.itoshi.ai`
5. Railway shows you a CNAME record, like:
   ```
   CNAME: app.itoshi.ai → random-name.up.railway.app
   ```
6. **Copy this value**

### 6b. In GoDaddy

1. Go to https://godaddy.com
2. **My Products** → **Domains** → **itoshi.ai** → **DNS**
3. Click **"Add"**
4. Configure:
   - **Type**: CNAME
   - **Name**: app
   - **Value**: [paste Railway's CNAME]
   - **TTL**: 600 seconds
5. Click **"Save"**

### 6c. Wait

- DNS takes 5-10 minutes to propagate
- Railway will auto-configure HTTPS when DNS is ready
- Check status in Railway's "Custom Domain" section

---

## Step 7: Done! 🎉

Visit: **https://app.itoshi.ai**

Your app is live!

---

## 📊 What You Get

| Feature | Details |
|---------|---------|
| **Auto HTTPS** | ✅ Free SSL certificate |
| **Auto Deploy** | ✅ Every git push deploys |
| **Monitoring** | ✅ Built-in metrics |
| **Logs** | ✅ Real-time log viewer |
| **Rollback** | ✅ One-click rollback |
| **Scaling** | ✅ Easy to upgrade plan |

---

## 💰 Pricing

- **Starter**: $5/month (includes $5 credit = free first month!)
- **Developer**: $20/month (more resources)
- **Team**: $60/month (team features)

You can start free with the $5 credit!

---

## 🔄 Updating Your App

```bash
cd /Users/paragchordia/Documents/code/itoshi

# Make your changes...

git add .
git commit -m "Update app"
git push

# Railway auto-deploys! ✨
```

That's it! No manual deployment needed.

---

## 📊 Monitoring & Logs

### View Logs

1. Go to Railway dashboard
2. Click your service
3. **"Deployments"** tab → Click latest deployment
4. See real-time logs

### View Metrics

1. Click **"Metrics"** tab
2. See:
   - CPU usage
   - Memory usage
   - Network traffic
   - Response times

### View Costs

1. Click project name (top left)
2. **"Usage"** → See current month's usage and costs

---

## 🚨 Troubleshooting

### Build Failed?

Check **"Deploy Logs"** tab for errors. Common issues:
- Missing dependencies in `requirements.txt`
- Python version mismatch

### App Crashes?

Check **"Runtime Logs"**:
1. Look for Python errors
2. Check if environment variables are set correctly
3. Make sure API keys are valid

### Can't Access App?

1. Check deployment is **"Active"** (green)
2. Verify custom domain DNS in GoDaddy
3. Try the Railway-provided domain first

### Custom Domain Not Working?

1. Wait 10-15 minutes for DNS propagation
2. Check DNS with: `dig app.itoshi.ai`
3. Verify CNAME is correct in GoDaddy
4. In Railway, click "Check" next to custom domain

---

## 📞 Getting Help

- Railway Docs: https://docs.railway.app
- Railway Discord: Join from website
- Railway Support: Click "?" in dashboard

---

## 🎯 Why This is Better Than AWS

| Feature | Railway | AWS EC2 |
|---------|---------|---------|
| Setup Time | 10 min | 30+ min |
| Cost | $5/mo | $42/mo |
| HTTPS Setup | Automatic | Manual |
| Deployment | Git push | Manual |
| Monitoring | Built-in | Setup required |
| Scaling | One click | Complex |
| Maintenance | Zero | Weekly updates |

---

## ✅ Checklist

- [ ] Code pushed to GitHub
- [ ] Railway account created
- [ ] App deployed
- [ ] Environment variables added
- [ ] Railway domain tested
- [ ] Custom domain added in Railway
- [ ] CNAME added in GoDaddy
- [ ] Waited 10 minutes for DNS
- [ ] https://app.itoshi.ai works!

---

**That's it! You're deployed! 🚀**

Any issues? Check the troubleshooting section above.

