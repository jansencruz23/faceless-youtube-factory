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

### Step 2: Generate Topic (AI)

1. Click **+** → Search "OpenAI" or "HTTP Request"
2. For **HTTP Request** to Groq:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Headers**: 
     - `Authorization`: `Bearer YOUR_GROQ_API_KEY`
     - `Content-Type`: `application/json`
   - **Body**:
   ```json
   {
     "model": "llama-3.3-70b-versatile",
     "messages": [
       {
         "role": "user", 
         "content": "Generate a unique topic for a 60-second video about surprising science facts. Return only the topic, one line."
       }
     ],
     "temperature": 0.9
   }
   ```

### Step 3: Create Project

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: POST
   - **URL**: `http://backend:8000/api/v1/projects`
   - **Headers**:
     - `Content-Type`: `application/json`
     - `Authorization`: `Bearer YOUR_CLERK_TOKEN`
   - **Body**:
   ```json
   {
     "title": "{{ $json.choices[0].message.content }}",
     "script_prompt": "{{ $json.choices[0].message.content }}",
     "auto_upload": true,
     "video_format": "vertical"
   }
   ```

### Step 4: Wait for Completion (Optional)

1. Add **Wait** node → 20 minutes
2. Add **HTTP Request** to check status:
   - **URL**: `http://backend:8000/api/v1/projects/{{ $json.id }}`

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

n8n has built-in nodes for:

| Platform | Node Name | Notes |
|----------|-----------|-------|
| TikTok | TikTok | Upload videos directly |
| Instagram | Facebook Graph API | Via connected Facebook page |
| Facebook | Facebook Graph API | Page posts |
| Twitter/X | Twitter | Direct posting |

After video is complete, add these nodes to upload to multiple platforms!

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
