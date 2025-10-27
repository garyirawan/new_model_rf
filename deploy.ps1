# Script untuk deploy ke cloud (Windows PowerShell)

Write-Host "🚀 Water Quality AI - Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (!(Test-Path ".git")) {
    Write-Host "📦 Initializing git repository..." -ForegroundColor Yellow
    git init
}

# Add all files
Write-Host "📝 Adding files to git..." -ForegroundColor Yellow
git add .

# Commit
$commitMsg = Read-Host "Enter commit message (default: 'Deploy to cloud')"
if ([string]::IsNullOrWhiteSpace($commitMsg)) {
    $commitMsg = "Deploy to cloud"
}
Write-Host "💾 Committing changes..." -ForegroundColor Yellow
git commit -m $commitMsg

# Push to GitHub
Write-Host "🔼 Pushing to GitHub..." -ForegroundColor Yellow
$repoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/repo.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "❌ Repository URL is required!" -ForegroundColor Red
    exit 1
}

# Add remote if not exists
git remote add origin $repoUrl 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote set-url origin $repoUrl
}

# Push
Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
git branch -M main
git push -u origin main

Write-Host ""
Write-Host "✅ Deployment preparation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Go to https://render.com"
Write-Host "2. Create a new Web Service"
Write-Host "3. Connect your GitHub repository"
Write-Host "4. Configure as per DEPLOYMENT_STEP_BY_STEP.md"
Write-Host ""
Write-Host "🔗 Your repository: $repoUrl" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
