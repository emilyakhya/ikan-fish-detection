# 🚀 IKAN Deployment Guide for DigitalOcean

This guide will help you deploy the IKAN Fish Detection system to DigitalOcean App Platform.

## 📋 Prerequisites

- A DigitalOcean account
- Your IKAN code in a Git repository (GitHub, GitLab, or Bitbucket)
- Basic knowledge of Git

## 🎯 Deployment Options

### Option 1: DigitalOcean App Platform (Recommended)

App Platform is the easiest way to deploy IKAN. It automatically handles:
- Container building
- SSL certificates
- Auto-scaling
- Health checks

#### Step 1: Prepare Your Repository

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Add deployment configuration"
   git push origin main
   ```

2. **Ensure these files are in your repository:**
   - `Dockerfile` ✅
   - `.dockerignore` ✅
   - `.do/app.yaml` ✅ (optional, can configure via UI)

#### Step 2: Deploy via DigitalOcean Dashboard

1. **Log in to DigitalOcean** and navigate to **App Platform**

2. **Create New App**
   - Click **"Create App"**
   - Choose **"GitHub"** (or your Git provider)
   - Select your IKAN repository
   - Select the branch (usually `main` or `master`)

3. **Configure the App**
   - **Name**: `ikan-fish-detection` (or your preferred name)
   - **Region**: Choose closest to your users (e.g., `nyc`, `sfo`, `sgp`)
   - **Build Command**: Leave default (uses Dockerfile)
   - **Run Command**: `python app.py`
   - **HTTP Port**: `8080`

4. **Environment Variables**
   Add these environment variables:
   ```
   FLASK_ENV=production
   PORT=8080
   PYTHONUNBUFFERED=1
   ```

5. **Resource Plan**
   - **Instance Size**: Start with `Basic` → `Basic XXS` ($5/month)
   - For better performance with YOLOv5, consider:
     - `Basic XS` ($12/month) - More CPU/RAM
     - `Professional` plans if you need GPU support

6. **Review and Deploy**
   - Review your configuration
   - Click **"Create Resources"**
   - Wait for build and deployment (5-10 minutes)

#### Step 3: Access Your App

Once deployed, DigitalOcean will provide:
- A URL like: `https://ikan-fish-detection-xxxxx.ondigitalocean.app`
- SSL certificate (automatic)
- Health check endpoint: `/api/health`

---

### Option 2: DigitalOcean Droplet (More Control)

If you need more control or GPU access, deploy to a Droplet.

#### Step 1: Create a Droplet

1. Go to **Droplets** → **Create Droplet**
2. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: 
     - **Basic**: $6/month (1GB RAM) - Minimum
     - **Basic**: $12/month (2GB RAM) - Recommended
     - **GPU**: If you need GPU acceleration
   - **Region**: Choose closest to users
   - **Authentication**: SSH keys (recommended) or password

#### Step 2: Connect and Setup

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose (optional)
apt install docker-compose -y

# Clone your repository
git clone https://github.com/your-username/IKAN.git
cd IKAN
```

#### Step 3: Build and Run

```bash
# Build Docker image
docker build -t ikan-app .

# Run container
docker run -d \
  --name ikan-app \
  -p 80:8080 \
  -e FLASK_ENV=production \
  -e PORT=8080 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  ikan-app
```

#### Step 4: Setup Nginx (Optional, for production)

```bash
# Install Nginx
apt install nginx -y

# Create Nginx config
cat > /etc/nginx/sites-available/ikan <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/ikan /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | HTTP port | `8080` |
| `FLASK_ENV` | Flask environment | `development` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

### Resource Requirements

**Minimum:**
- CPU: 1 vCPU
- RAM: 1GB
- Storage: 10GB

**Recommended:**
- CPU: 2 vCPU
- RAM: 2GB
- Storage: 25GB

**For GPU (if available):**
- GPU: 1x NVIDIA GPU
- CUDA support required

---

## 📝 Post-Deployment

### 1. Test Health Endpoint

```bash
curl https://your-app-url.ondigitalocean.app/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "pytorch": "2.x.x",
  "cuda_available": false
}
```

### 2. Test File Upload

1. Open your app URL in a browser
2. Upload a test image
3. Run detection
4. Verify results

### 3. Monitor Logs

**App Platform:**
- Go to your app → **Runtime Logs**

**Droplet:**
```bash
docker logs ikan-app -f
```

---

## 🔒 Security Considerations

1. **File Upload Limits**: Already set to 100MB max
2. **CORS**: Configured for cross-origin requests
3. **Environment Variables**: Store secrets in DigitalOcean environment variables
4. **SSL**: Automatically handled by App Platform

---

## 🐛 Troubleshooting

### Build Fails

**Issue**: Docker build timeout or memory error
**Solution**: 
- Increase build timeout in App Platform settings
- Use smaller base image or optimize Dockerfile

### App Crashes on Startup

**Issue**: Port binding error
**Solution**: Ensure `PORT` environment variable is set to `8080`

### Model Not Found

**Issue**: `yolov5s.pt` not found
**Solution**: 
- Ensure model file is in repository (or download at runtime)
- Check file paths in `app.py`

### Out of Memory

**Issue**: App runs out of memory during detection
**Solution**:
- Upgrade to larger instance size
- Reduce image size in detection (`imgsz` parameter)
- Process images in batches

---

## 📊 Monitoring

### App Platform Metrics

- CPU usage
- Memory usage
- Request count
- Response times

### Custom Monitoring

Add monitoring endpoints or integrate with:
- DigitalOcean Monitoring
- Datadog
- New Relic

---

## 🔄 Updates and CI/CD

### Automatic Deployments

App Platform automatically deploys when you push to your main branch.

### Manual Deployment

```bash
# Make changes
git add .
git commit -m "Update app"
git push origin main

# App Platform will automatically rebuild and deploy
```

---

## 💰 Cost Estimation

**App Platform (Basic XXS):**
- $5/month per instance
- Additional costs for:
  - Bandwidth (1TB free)
  - Storage ($0.10/GB/month)

**Droplet (Basic):**
- $6/month (1GB RAM)
- $12/month (2GB RAM)
- Additional costs for:
  - Bandwidth (1TB free)
  - Snapshots ($0.05/GB/month)

---

## 📚 Additional Resources

- [DigitalOcean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [Docker Documentation](https://docs.docker.com/)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)

---

## ✅ Checklist

- [ ] Code pushed to Git repository
- [ ] Dockerfile created and tested locally
- [ ] Environment variables configured
- [ ] App deployed to DigitalOcean
- [ ] Health check passing
- [ ] File upload working
- [ ] Detection working
- [ ] SSL certificate active
- [ ] Monitoring configured

---

**Need Help?** Check the [IKAN README](./README.md) or open an issue on GitHub.