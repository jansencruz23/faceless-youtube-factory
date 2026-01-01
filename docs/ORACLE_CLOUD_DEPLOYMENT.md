# Oracle Cloud Deployment Guide

Deploy Faceless YouTube Factory to Oracle Cloud Always Free tier for 24/7 automated video generation.

## What You Get (Free Forever)

| Resource | Free Amount |
|----------|-------------|
| ARM VM | 4 OCPUs, 24GB RAM |
| Storage | 200GB |
| Outbound | 10TB/month |

---

## Step 1: Create Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com)
2. Click "Sign Up" → "Cloud Free Tier"
3. Enter your details (credit card required for verification, never charged)
4. Wait for account creation (usually instant, sometimes 30 min)

---

## Step 2: Create ARM Instance

1. Go to **Compute → Instances → Create Instance**
2. Configure:
   - **Name**: `youtube-factory`
   - **Image**: Ubuntu 22.04 (ARM)
   - **Shape**: Click "Change Shape" → Ampere → VM.Standard.A1.Flex
     - **OCPUs**: 4
     - **Memory**: 24GB
   - **Add SSH Key**: Paste your public key or generate new
3. Click **Create**

> ⚠️ If you see "Out of capacity", try these regions: **Ashburn, Phoenix, London, Frankfurt**

---

## Step 3: Connect to Your Instance

```bash
# Replace with your instance's public IP
ssh ubuntu@<YOUR_PUBLIC_IP>
```

---

## Step 4: Install Docker

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Logout and login for group changes
exit
```

SSH back in, then verify:
```bash
docker --version
docker compose version
```

---

## Step 5: Clone Your Repository

```bash
# Clone repo (or use git pull if already there)
git clone https://github.com/YOUR_USERNAME/faceless-youtube-factory.git
cd faceless-youtube-factory
```

---

## Step 6: Configure Environment

Create `.env` file:
```bash
nano .env
```

Add your configuration:
```bash
# Database
DB_USER=youtube_factory
DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE
DB_NAME=youtube_factory

# API Keys
GROQ_API_KEY=your_groq_api_key
HF_TOKEN=your_huggingface_token
TOKEN_ENCRYPTION_KEY=your_fernet_key

# Google OAuth (for YouTube upload)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
OAUTH_REDIRECT_URI=https://your-domain.com/api/v1/youtube/callback

# Clerk Auth
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# URLs (update with your domain)
FRONTEND_URL=https://your-domain.com
NEXT_PUBLIC_API_URL=https://your-domain.com
NEXT_PUBLIC_WS_URL=wss://your-domain.com

# Scheduler
SCHEDULER_ENABLED=true
```

Generate Fernet key if needed:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Step 7: Deploy

```bash
# Use the cloud-specific compose file (CPU mode)
docker compose -f docker-compose.cloud.yml up -d

# Check logs
docker compose -f docker-compose.cloud.yml logs -f
```

---

## Step 8: Set Up HTTPS (Optional but Recommended)

### Using Caddy (Easiest)

1. Install Caddy:
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

2. Create Caddyfile:
```bash
sudo nano /etc/caddy/Caddyfile
```

```
your-domain.com {
    # Frontend
    reverse_proxy localhost:3000

    # API (backend)
    handle /api/* {
        reverse_proxy localhost:8000
    }
    
    # WebSocket
    handle /ws/* {
        reverse_proxy localhost:8000
    }
}
```

3. Restart Caddy:
```bash
sudo systemctl restart caddy
```

---

## Step 9: Open Firewall Ports

In Oracle Cloud Console:
1. Go to **Networking → Virtual Cloud Networks**
2. Click your VCN → **Security Lists**
3. Add **Ingress Rules**:
   - Port 80 (HTTP)
   - Port 443 (HTTPS)

On the instance:
```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

---

## Using the Scheduler

Once deployed, create scheduled jobs via the API:

```bash
# Create a daily job at 10 AM PH time (2 AM UTC)
curl -X POST "https://your-domain.com/api/v1/scheduler" \
  -H "Authorization: Bearer YOUR_CLERK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Science Video",
    "cron_expression": "0 2 * * *",
    "topic_category": "surprising science facts",
    "video_format": "vertical",
    "auto_upload": true
  }'
```

### Cron Expression Examples

| Schedule | Cron Expression |
|----------|-----------------|
| 10 AM PH daily | `0 2 * * *` |
| 8 PM PH daily | `0 12 * * *` |
| Every 6 hours | `0 */6 * * *` |
| Mon/Wed/Fri 9 AM PH | `0 1 * * 1,3,5` |

---

## Troubleshooting

### Check if containers are running
```bash
docker compose -f docker-compose.cloud.yml ps
```

### View logs
```bash
docker compose -f docker-compose.cloud.yml logs backend -f
docker compose -f docker-compose.cloud.yml logs frontend -f
```

### Restart services
```bash
docker compose -f docker-compose.cloud.yml restart
```

### Check scheduler is running
Look for this in backend logs:
```
Scheduler started
Loaded X scheduled jobs
```

---

## Performance Notes

- **Image generation**: ~5-10 min per image (CPU mode)
- **Full video**: ~15-30 min per short video
- **Recommended**: Schedule during off-peak hours (night time)
