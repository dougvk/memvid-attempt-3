# VPS Deployment Guide

This guide explains how to deploy the memvid search API to a Virtual Private Server (VPS).

## Architecture Overview

- **Local Machine**: Handles heavy processing (indexing)
- **VPS**: Lightweight API server (serving searches only)
- **Upload Process**: Sync 3 index files (~250MB) when new episodes are added

## VPS Requirements

### Minimum Specifications
- **RAM**: 512MB (1GB recommended)
- **CPU**: 1 vCPU
- **Storage**: 1GB free space
- **OS**: Ubuntu 20.04+ or Debian 11+

### Recommended VPS Providers
- **DigitalOcean**: Basic Droplet ($6/month) - 1GB RAM
- **Linode**: Nanode ($5/month) - 1GB RAM
- **Vultr**: Regular Cloud Compute ($6/month) - 1GB RAM
- **Hetzner**: CX11 (€3.29/month) - 2GB RAM (best value)

## Initial VPS Setup

### 1. Install Python and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Create project directory
sudo mkdir -p /opt/podcast-api
sudo chown $USER:$USER /opt/podcast-api
cd /opt/podcast-api
```

### 2. Create Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv memvid-env
source memvid-env/bin/activate

# Install required packages
pip install memvid fastapi uvicorn
```

### 3. Copy API Files

```bash
# Copy search_api.py from your local machine
scp search_api.py user@your-vps-ip:/opt/podcast-api/

# Create output directory for index files
mkdir -p /opt/podcast-api/output
```

## Systemd Service Configuration

### 1. Create Service File

Create `/etc/systemd/system/podcast-api.service`:

```ini
[Unit]
Description=Podcast Search API
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/opt/podcast-api
Environment="PATH=/opt/podcast-api/memvid-env/bin"
ExecStart=/opt/podcast-api/memvid-env/bin/python search_api.py --index-base output/podcasts_2048_chunk --port 8000 --host 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable podcast-api

# Start the service
sudo systemctl start podcast-api

# Check status
sudo systemctl status podcast-api
```

## Uploading Index Files

### Initial Upload

From your local machine:

```bash
# Upload all index files
rsync -avz --progress output/podcasts_2048_chunk* user@your-vps-ip:/opt/podcast-api/output/
```

### Update Process

When you've indexed new episodes:

1. Create new index locally:
   ```bash
   python3 file_chat.py --input-dir podcast_transcripts/ --chunk-size 2048 --overlap 307 --workers 8 --memory-name podcasts_2048_chunk
   ```

2. Upload to VPS:
   ```bash
   ./upload.sh
   ```

3. Restart service:
   ```bash
   ssh user@your-vps-ip 'sudo systemctl restart podcast-api'
   ```

## Zero-Downtime Updates (Optional)

For zero-downtime updates:

1. Upload with timestamp:
   ```bash
   TIMESTAMP=$(date +%Y%m%d_%H%M%S)
   rsync -avz output/podcasts_2048_chunk* user@vps:/opt/podcast-api/output/temp_$TIMESTAMP/
   ```

2. Switch files and restart:
   ```bash
   ssh user@vps 'cd /opt/podcast-api && \
     mv output output_old && \
     mv output/temp_'$TIMESTAMP' output && \
     sudo systemctl restart podcast-api && \
     rm -rf output_old'
   ```

## Nginx Reverse Proxy (Optional)

### 1. Install Nginx

```bash
sudo apt install nginx -y
```

### 2. Configure Nginx

Create `/etc/nginx/sites-available/podcast-api`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/podcast-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. SSL with Let's Encrypt (Optional)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Monitoring

### Check Service Logs

```bash
# View recent logs
sudo journalctl -u podcast-api -n 50

# Follow logs in real-time
sudo journalctl -u podcast-api -f
```

### Check Memory Usage

```bash
# Check API memory usage
ps aux | grep search_api.py

# System memory
free -h
```

## Firewall Configuration

```bash
# Allow SSH and HTTP/HTTPS
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443

# If not using nginx, allow API port
sudo ufw allow 8000

# Enable firewall
sudo ufw enable
```

## Troubleshooting

### Service Won't Start
- Check logs: `sudo journalctl -u podcast-api -n 100`
- Verify Python path: `which python3`
- Check file permissions: `ls -la /opt/podcast-api/`

### Out of Memory
- Check memory: `free -h`
- Restart service: `sudo systemctl restart podcast-api`
- Consider upgrading VPS

### Can't Connect
- Check firewall: `sudo ufw status`
- Verify service is running: `sudo systemctl status podcast-api`
- Test locally: `curl http://localhost:8000/health`

## Performance Notes

Based on testing with 21,861 chunks:
- **Memory Usage**: ~360MB after loading index
- **Query Time**: 100-170ms per search
- **CPU Usage**: <5% during queries
- **Handles**: 10+ concurrent requests easily