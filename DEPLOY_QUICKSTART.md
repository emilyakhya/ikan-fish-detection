# ⚡ Quick Start: Deploy IKAN to DigitalOcean

## 🎯 Fastest Way (5 minutes)

### 1. Push to GitHub
```bash
git add .
git commit -m "Add deployment files"
git push origin main
```

### 2. Deploy via DigitalOcean Dashboard

1. Go to: https://cloud.digitalocean.com/apps
2. Click **"Create App"**
3. Connect your GitHub repository
4. Select your IKAN repository
5. DigitalOcean will auto-detect the Dockerfile
6. Click **"Create Resources"**
7. Wait 5-10 minutes for deployment

### 3. Done! 🎉

Your app will be available at: `https://your-app-name.ondigitalocean.app`

---

## 🔧 Quick Configuration

### Required Environment Variables:
- `PORT=8080` (auto-set by DigitalOcean)
- `FLASK_ENV=production` (recommended)

### Recommended Instance Size:
- **Basic XXS** ($5/month) - For testing
- **Basic XS** ($12/month) - For production

---

## 📋 Files Created

✅ `Dockerfile` - Container configuration
✅ `.dockerignore` - Excludes unnecessary files
✅ `.do/app.yaml` - App Platform config (optional)
✅ `DEPLOYMENT.md` - Full deployment guide

---

## 🧪 Test Locally Before Deploying

```bash
# Build Docker image
docker build -t ikan-app .

# Run locally
docker run -p 8080:8080 -e PORT=8080 ikan-app

# Test in browser
open http://localhost:8080
```

---

## 🆘 Need Help?

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.