#!/bin/bash
# Helper script to push code to GitHub for Railway/Render/etc deployment

echo "=========================================="
echo "🚀 Deploy Itoshi to GitHub"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
else
    echo "📝 Adding files to git..."
    git add .
    
    echo ""
    echo "Enter commit message (or press Enter for default):"
    read -r commit_msg
    
    if [ -z "$commit_msg" ]; then
        commit_msg="Update application"
    fi
    
    echo "💾 Committing changes..."
    git commit -m "$commit_msg"
fi

# Check if remote exists
if git remote | grep -q "origin"; then
    echo "✅ Remote 'origin' already configured"
    echo ""
    echo "🚀 Pushing to GitHub..."
    git push origin main || git push origin master
else
    echo ""
    echo "❓ No remote configured yet."
    echo ""
    echo "📋 Next steps:"
    echo "1. Create a new repository on GitHub (https://github.com/new)"
    echo "2. Name it: itoshi or itoshi-app"
    echo "3. DO NOT initialize with README"
    echo "4. Copy the repository URL (e.g., https://github.com/USERNAME/itoshi.git)"
    echo ""
    echo "Enter your GitHub repository URL:"
    read -r repo_url
    
    if [ -z "$repo_url" ]; then
        echo "❌ No URL provided. Exiting."
        exit 1
    fi
    
    echo "🔗 Adding remote..."
    git remote add origin "$repo_url"
    
    echo "🚀 Pushing to GitHub..."
    git branch -M main
    git push -u origin main
fi

echo ""
echo "=========================================="
echo "✅ Code pushed to GitHub!"
echo "=========================================="
echo ""
echo "📋 Next Steps for Railway:"
echo "1. Go to https://railway.app"
echo "2. Sign up/Login with GitHub"
echo "3. New Project → Deploy from GitHub repo"
echo "4. Select your repository"
echo "5. Add environment variables:"
echo "   - OPENAI_API_KEY"
echo "   - KLING_ACCESS_KEY"
echo "   - KLING_SECRET_KEY"
echo "6. Settings → Generate Domain"
echo "7. Settings → Custom Domain → app.itoshi.ai"
echo "8. Copy CNAME and add to GoDaddy DNS"
echo ""
echo "💰 Cost: \$5/month (includes \$5 free credit)"
echo ""
echo "📋 Next Steps for Render:"
echo "1. Go to https://render.com"
echo "2. Sign up/Login with GitHub"
echo "3. New → Web Service"
echo "4. Connect your repository"
echo "5. Choose Starter plan (\$7/month)"
echo "6. Add environment variables"
echo "7. Custom Domain → app.itoshi.ai"
echo ""
echo "=========================================="

