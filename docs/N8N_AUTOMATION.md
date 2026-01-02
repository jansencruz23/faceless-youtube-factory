# n8n Automation Setup

Automate video creation using n8n workflow automation.

## Quick Start

1. Start your stack:
```bash
docker-compose up -d
```

2. Open n8n: [http://localhost:5678](http://localhost:5678)
   - Username: `admin` (or N8N_USER from .env)
   - Password: `password` (or N8N_PASSWORD from .env)

---

## Create Your First Workflow

### Step 1: Add Schedule Trigger

1. Click **Add first step** → Search "Schedule"
2. Select **Schedule Trigger**
3. Configure:
   - **Trigger Interval**: Custom (Cron)
   - **Cron Expression**: `0 */5 * * *` (every 5 hours)

### Step 2: Generate Topic (Optional - AI)

You can use n8n's AI nodes or Groq directly to generate topics:

1. Click **+** → Search "HTTP Request"
2. Configure for Groq API:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Headers**: 
     - `Authorization`: `Bearer YOUR_GROQ_API_KEY`
     - `Content-Type`: `application/json`
   - **Body (JSON)**:
   ```json
   {
     "model": "llama-3.3-70b-versatile",
     "messages": [{"role": "user", "content": "Generate a unique topic for a 60-second video about surprising science facts. Return only the topic."}],
     "temperature": 0.9
   }
   ```

### Step 3: Create Project (Use Automation API)

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: POST
   - **URL**: `http://backend:8000/api/v1/automation/generate`
   - **Headers**:
     - `X-API-Key`: `YOUR_AUTOMATION_API_KEY` (from .env)
     - `Content-Type`: `application/json`
   - **Body (JSON)**:
   ```json
   {
     "topic": "{{ $('Generate Topic').item.json.choices[0].message.content.replace(/^\"|\"$/g, '') }}",
     "video_format": "vertical",
     "background_video": "preset:minecraft_parkour",
     "background_music": "preset:dreamland",
     "music_volume": 0.1,
     "image_mode": "none",
     "enable_captions": true,
     "auto_upload": false
   }
   ```

#### Available Options:

| Field | Options | Description |
|-------|---------|-------------|
| `video_format` | `"vertical"`, `"horizontal"` | Video orientation |
| `background_video` | `"preset:minecraft"`, `"preset:subway"`, `null`, URL | For vertical videos |
| `background_music` | `"preset:lofi"`, `"preset:energetic"`, `null`, URL | Background music |
| `music_volume` | `0.0` to `1.0` | Music volume level |
| `image_mode` | `"none"`, `"per_scene"`, `"shared"` | Image generation mode |
| `enable_captions` | `true`, `false` | Show captions |
| `auto_upload` | `true`, `false` | Auto-upload to YouTube |

### Step 4: Check Status (Optional)

1. Add **Wait** node → 20 minutes
2. Add **HTTP Request**:
   - **URL**: `http://backend:8000/api/v1/automation/status/{{ $json.project_id }}`
   - **Headers**: `X-API-Key`: `YOUR_AUTOMATION_API_KEY`

---

## Example Cron Expressions

| Schedule | Cron Expression |
|----------|-----------------|
| Every 5 hours | `0 */5 * * *` |
| 10 AM daily (PH) | `0 2 * * *` |
| Every 3 hours | `0 */3 * * *` |
| 8 AM and 8 PM | `0 0,12 * * *` |

---

## Run on PC Startup

n8n starts automatically with Docker Compose. When your PC boots:

1. Docker Desktop starts (enable in Windows Settings → Apps → Startup)
2. Your containers start automatically (`restart: unless-stopped`)
3. n8n loads saved workflows and runs scheduled jobs

---

## Multi-Platform Upload

After your video is complete, add upload nodes to post to social media:

### YouTube (via your app)

Already handled by `auto_upload: true` in your request!

### TikTok

1. Click **+** → Search **"TikTok"**
2. **Auth**: Connect your TikTok Creator account
3. **Operation**: Upload Video
4. **Video**: Use the video file from your project (download first)

> ⚠️ TikTok API requires Creator account approval

### Facebook & Instagram

1. Click **+** → Search **"Facebook Graph API"**
2. **Auth**: Connect Facebook Business account with Instagram linked
3. For **Instagram Reels**:
   - Container: Create → Reel
   - Publish: Container ID

> ⚠️ Requires Meta Business verification

### Twitter/X

1. Click **+** → Search **"Twitter"**
2. **Auth**: Connect Twitter Developer account
3. **Operation**: Create Tweet with Media

### Alternative: Manual Upload via Folder

The easiest approach - save videos to a synced folder:

1. After video completes, download to local folder
2. Use Google Drive / Dropbox to sync
3. Manually upload from phone (or use scheduling apps like Later, Buffer)

### Finding Your Generated Video

After status shows `completed` or `published`:
- Video path: `http://localhost:8000/static/shorts/{project_id}.mp4`
- Or check your dashboard: http://localhost:3000

---

## Troubleshooting

### n8n not accessible
```bash
docker-compose logs n8n
```

### Workflow not running
- Check if workflow is **Active** (toggle in top right)
- Check execution history in n8n

### Reset n8n password
```bash
docker-compose exec n8n n8n user-management:reset
```
