#!/bin/bash
# Quick deployment script for DigitalOcean App Platform
# Usage: ./deploy.sh

echo "🚀 IKAN Deployment Script for DigitalOcean"
echo "=========================================="
echo ""

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo "⚠️  doctl CLI not found. Installing..."
    echo "Visit: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    exit 1
fi

# Check if logged in
if ! doctl auth list &> /dev/null; then
    echo "⚠️  Not logged in to DigitalOcean"
    echo "Run: doctl auth init"
    exit 1
fi

echo "✅ DigitalOcean CLI configured"
echo ""

# Check if app.yaml exists
if [ ! -f ".do/app.yaml" ]; then
    echo "⚠️  .do/app.yaml not found"
    echo "Creating from template..."
    mkdir -p .do
    # You can customize this
fi

echo "📦 Building Docker image locally (test)..."
docker build -t ikan-app:test .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo "✅ Docker build successful"
echo ""
echo "📝 Next steps:"
echo "1. Push your code to GitHub/GitLab/Bitbucket"
echo "2. Go to DigitalOcean App Platform"
echo "3. Create new app from your repository"
echo "4. Or use: doctl apps create --spec .do/app.yaml"
echo ""
echo "🌐 Or deploy via web UI:"
echo "   https://cloud.digitalocean.com/apps"