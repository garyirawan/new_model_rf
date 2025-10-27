#!/bin/bash
# Script untuk deploy ke cloud

echo "🚀 Water Quality AI - Deployment Script"
echo "========================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Commit
echo "💾 Committing changes..."
read -p "Enter commit message (default: 'Deploy to cloud'): " commit_msg
commit_msg=${commit_msg:-"Deploy to cloud"}
git commit -m "$commit_msg"

# Push to GitHub
echo "🔼 Pushing to GitHub..."
read -p "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): " repo_url

if [ -z "$repo_url" ]; then
    echo "❌ Repository URL is required!"
    exit 1
fi

# Add remote if not exists
git remote add origin "$repo_url" 2>/dev/null || git remote set-url origin "$repo_url"

# Push
git push -u origin main

echo "✅ Deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Go to https://render.com"
echo "2. Create a new Web Service"
echo "3. Connect your GitHub repository"
echo "4. Configure as per DEPLOYMENT_STEP_BY_STEP.md"
echo ""
echo "🔗 Your repository: $repo_url"
