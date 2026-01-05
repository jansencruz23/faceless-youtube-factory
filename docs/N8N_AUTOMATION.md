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

## Avoiding Duplicate Topics (AI Semantic Check)

Simple string matching can't detect that "Why you forget names" and "The science of forgetting" are the same topic. Use AI to detect semantic duplicates.

### Prerequisites

1. Create a Google Sheet with columns:
   - **A**: Date
   - **B**: Topic  
   - **C**: Project ID
   - **D**: Status

2. In n8n, connect your Google account:
   - Go to **Credentials** → **Add Credential** → **Google Sheets OAuth2**
   - Follow the OAuth flow

### Complete Workflow (7 nodes)

```
Schedule → Get Topics from Sheet → Generate New Topic → Check if Duplicate (AI) → IF duplicate?
                                                                                    ├─ YES → back to Generate
                                                                                    └─ NO → Create Project → Log to Sheet
```

### Step-by-Step Instructions

#### Node 1: Schedule Trigger

1. Click **Add first step** → Search "Schedule"
2. Configure:
   - **Trigger Interval**: Hours
   - **Hours Between Triggers**: 5

#### Node 2: Get Existing Topics (Google Sheets)

1. Click **+** → Search "Google Sheets"
2. Configure:
   - **Credential**: Select your Google Sheets credential
   - **Operation**: Read Rows
   - **Document**: Select your topic tracker spreadsheet
   - **Sheet**: Sheet1 (or your sheet name)
   - **Options** → **Data Location**: First row is header
3. This outputs all your existing topics

#### Node 3: Generate New Topic (Groq)

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Authentication**: Header Auth
     - Name: `Authorization`
     - Value: `Bearer YOUR_GROQ_API_KEY`
   - **Headers**: Add `Content-Type`: `application/json`
   - **Body Content Type**: JSON
   - **Body**:
   ```json
   {
     "model": "llama-3.3-70b-versatile",
     "messages": [{
       "role": "user",
       "content": "Generate a unique, engaging topic for a 60-second vertical video about psychology and human behavior facts. The topic should be specific and interesting. Return ONLY the topic text, nothing else."
     }],
     "temperature": 0.9
   }
   ```

#### Node 4: Check for Semantic Duplicates (Groq AI)

1. Click **+** → Search "HTTP Request" 
2. Rename to "Check Duplicate"
3. Configure:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Authentication**: Same as above
   - **Body**:
   ```json
   {
     "model": "llama-3.3-70b-versatile",
     "messages": [{
       "role": "user",
       "content": "I have these existing video topics:\n{{ $('Get Existing Topics').all().map(item => '- ' + item.json.Topic).join('\\n') }}\n\nNew proposed topic: \"{{ $('Generate New Topic').item.json.choices[0].message.content }}\"\n\nIs the new topic semantically too similar to ANY existing topic? Topics about the same concept but with different wording ARE duplicates. Answer with ONLY 'YES' or 'NO'."
     }],
     "temperature": 0
   }
   ```

#### Node 5: IF Node (Check Result)

1. Click **+** → Search "IF"
2. Configure:
   - **Condition**: String → Contains
   - **Value 1**: `{{ $json.choices[0].message.content }}`
   - **Value 2**: `YES`
   - **Case Sensitive**: No

3. Connect:
   - **True output** (is duplicate) → Loop back to "Generate New Topic" node
   - **False output** (is unique) → Continue to "Create Project"

#### Node 6: Create Project (Your API)

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: POST
   - **URL**: `http://backend:8000/api/v1/automation/generate`
   - **Headers**: 
     - `X-API-Key`: `YOUR_AUTOMATION_API_KEY`
     - `Content-Type`: `application/json`
   - **Body**:
   ```json
   {
     "topic": "{{ $('Generate New Topic').item.json.choices[0].message.content.replace(/^\"|\"$/g, '') }}",
     "video_format": "vertical",
     "background_video": "preset:minecraft_parkour",
     "background_music": "preset:dreamland",
     "music_volume": 0.1,
     "enable_captions": true,
     "auto_upload": false
   }
   ```

#### Node 7: Log to Google Sheet

1. Click **+** → Search "Google Sheets"
2. Configure:
   - **Operation**: Append Row
   - **Document**: Your topic tracker
   - **Sheet**: Sheet1
   - **Columns**:
     - **Date**: `{{ $now.format('YYYY-MM-DD HH:mm') }}`
     - **Topic**: `{{ $('Generate New Topic').item.json.choices[0].message.content }}`
     - **Project ID**: `{{ $json.project_id }}`
     - **Status**: `generating`

### Connecting the Loop

To create the regeneration loop:

1. From the IF node's **True** output (duplicate detected)
2. Draw a line back to the "Generate New Topic" node
3. n8n will create a loop that retries until a unique topic is found

### Important Settings

- Set a **max retry** in the IF node settings to prevent infinite loops (e.g., 5 retries)
- After max retries, you can either:
  - Stop the workflow
  - Use the topic anyway with a warning
  - Send yourself a notification

### Testing Your Workflow

1. Click **Test Workflow** in n8n
2. Watch each node execute
3. Check that:
   - Topics are read from sheet
   - New topic is generated
   - AI correctly identifies duplicates
   - Unique topics get logged

### Activate the Workflow

1. Toggle the **Active** switch in the top right
2. Your workflow will now run automatically every 5 hours

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

