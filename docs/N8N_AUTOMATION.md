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
3. This outputs all your existing topics (one item per row)

#### Node 2.5: Aggregate (Prevent Multiple Executions)

Without this node, subsequent nodes run once per sheet row. Add Aggregate to combine all rows into a single item:

1. Click **+** → Search "Aggregate"
2. Configure:
   - **Aggregate**: All Item Data (Into a Single List)
3. Now subsequent nodes only run once

#### Node 3: Generate New Topic (Groq)

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Authentication**: Header Auth
     - Name: `Authorization`
     - Value: `Bearer YOUR_GROQ_API_KEY`
   - **Headers**: Add `Content-Type`: `application/json`
   - **Body Content Type**: n8n (for expressions)
   - **Specify Body**: Using Fields Below

3. **IMPORTANT**: Instead of JSON mode, use the expression builder:
   - Click **Add Field** → Name: `model`, Value: `llama-3.3-70b-versatile`
   - Click **Add Field** → Name: `temperature`, Value: `0.9`
   - Click **Add Field** → Name: `messages`, Value (toggle to Expression):

```javascript
[{
  "role": "user",
  "content": "Generate a unique, engaging topic for a 60-second vertical video about psychology and human behavior facts.\n\nIMPORTANT RULES:\n1. Do NOT use quotation marks in your response\n2. Do NOT include any special characters\n3. Return ONLY the plain topic text, nothing else\n4. Make it COMPLETELY DIFFERENT from these already-used topics:\n" + (($('Get Existing Topics').all() || []).filter(item => item.json.Topic).map(item => '- ' + String(item.json.Topic).replace(/"/g, "'").replace(/\n/g, ' ')).join('\n') || '(No existing topics yet)')
}]
```

**Alternative: Full Expression Mode Body**

If the above doesn't work, set **Body Content Type** to **Expression** and paste:

```javascript
{{ JSON.stringify({
  model: "llama-3.3-70b-versatile",
  messages: [{
    role: "user",
    content: "Generate a unique, engaging topic for a 60-second vertical video about psychology and human behavior facts.\n\nIMPORTANT RULES:\n1. Do NOT use quotation marks\n2. Do NOT include special characters\n3. Return ONLY plain topic text\n4. Make it COMPLETELY DIFFERENT from these used topics:\n" + (($('Get Existing Topics').all() || []).filter(i => i.json.Topic).map(i => '- ' + String(i.json.Topic).replace(/"/g, "'").replace(/\n/g, ' ')).join('\n') || '(No existing topics)')
  }],
  temperature: 0.9
}) }}

#### Node 4: Check for Semantic Duplicates (Groq AI)

> **Note**: This node is optional. Since Node 3 already includes existing topics in the prompt, this duplicate check is extra protection. You can skip this node if you want a simpler workflow.

1. Click **+** → Search "HTTP Request" 
2. Rename to "Check Duplicate"
3. Configure:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Authentication**: Same as above
   - **Body Content Type**: Expression
   - **Body**:
   
```javascript
{{ JSON.stringify({
  model: "llama-3.3-70b-versatile",
  messages: [{
    role: "user",
    content: "I have these existing video topics:\n" + ($('Aggregate').first().json.data || []).filter(i => i.Topic).map(i => '- ' + i.Topic).join('\n') + "\n\nNew proposed topic: \"" + $('Generate New Topic').first().json.choices[0].message.content + "\"\n\nIs the new topic semantically too similar to ANY existing topic? Answer ONLY 'YES' or 'NO'."
  }],
  temperature: 0
}) }}
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
   - **Body Content Type**: Expression
   - **Body**:

```javascript
{{ JSON.stringify({
  topic: $('Generate New Topic').first().json.choices[0].message.content,
  category: "psychology",
  video_format: "vertical",
  background_video: "preset:minecraft_parkour",
  background_music: "preset:dreamland",
  music_volume: 0.1,
  enable_captions: true,
  auto_upload: false
}) }}
```
   
   > **Tip**: Use a different `category` value for each n8n workflow/channel (e.g., "psychology", "motivation", "tech facts"). Videos will be grouped by category in the UI.

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

## Polling for Completion (Update Status)

To update the status in Google Sheets when the video is done, add polling nodes after "Create Project".

### Add Polling Nodes

#### Node 8: Wait

1. Click **+** after "Log to Google Sheet" → Search "Wait"
2. Configure:
   - **Resume**: After Time Interval
   - **Wait Amount**: 2
   - **Wait Unit**: Minutes

#### Node 9: Check Status (HTTP Request)

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: GET
   - **URL**: `http://backend:8000/api/v1/automation/status/{{ $('Create Project').item.json.project_id }}`
   - **Headers**: `X-API-Key`: `YOUR_AUTOMATION_API_KEY`

#### Node 10: IF Status Complete

1. Click **+** → Search "IF"
2. Configure:
   - **Condition**: String → Equals
   - **Value 1**: `{{ $json.status }}`
   - **Value 2**: `completed`

3. Connect:
   - **True output** → Generate Metadata
   - **False output** → Check if failed, or loop back to Wait

#### Node 11: Generate Metadata (Groq)

1. Click **+** → Search "HTTP Request"
2. Configure:
   - **Method**: POST
   - **URL**: `https://api.groq.com/openai/v1/chat/completions`
   - **Authentication**: Header Auth (same as Generate Topic)
   - **Body**:
   ```json
   {
     "model": "llama-3.3-70b-versatile",
     "messages": [{
       "role": "user",
       "content": "Based on this video topic: {{ JSON.stringify($('Generate New Topic').item.json.choices[0].message.content) }}\n\nGenerate social media metadata. Return ONLY valid JSON with no extra text:\n{\"title\": \"catchy title max 60 chars\", \"description\": \"engaging description max 150 chars\", \"hashtags\": \"#tag1 #tag2 #tag3 etc 10 hashtags\"}"
     }],
     "temperature": 0.7
   }
   ```

#### Node 12: Update Sheet Row (Google Sheets)

1. Click **+** → Search "Google Sheets"
2. Configure:
   - **Operation**: Update Row
   - **Document**: Your topic tracker
   - **Sheet**: Sheet1
   - **Row Number**: Find by Project ID (use Lookup or store row number earlier)
   - **Columns to Update**:
     - **Status**: `completed`
     - **Video Link**: `http://localhost:8000/static/shorts/{{ $('Create Project').item.json.project_id }}.mp4`
     - **Title**: `{{ JSON.parse($('Generate Metadata').item.json.choices[0].message.content).title }}`
     - **Description**: `{{ JSON.parse($('Generate Metadata').item.json.choices[0].message.content).description }}`
     - **Hashtags**: `{{ JSON.parse($('Generate Metadata').item.json.choices[0].message.content).hashtags }}`

> **Tip**: If JSON.parse fails, add a **Code** node before to safely extract the JSON from the LLM response.

---

## Google Sheets Setup (Enhanced)

### Recommended Columns

| Column | Header | Purpose |
|--------|--------|---------|
| A | Date | When created |
| B | Topic | Video topic |
| C | Project ID | For API reference |
| D | Status | generating/completed/failed |
| E | Video Link | Link to video file |
| F | Title | Generated catchy title |
| G | Description | Social media description |
| H | Hashtags | Generated hashtags |
| I | YouTube | Checkbox |
| J | TikTok | Checkbox |
| K | Instagram | Checkbox |
| L | Facebook | Checkbox |
| M | Notes | Any comments |

### Color-Coded Status with Dropdown

#### Step 1: Create the Dropdown

1. Select the Status column cells (D2:D1000 or your range)
2. **Data** → **Data validation**
3. Configure:
   - **Criteria**: Dropdown
   - **Options**: `pending`, `generating`, `completed`, `failed`
4. Click **Done**

#### Step 2: Writing to Dropdown via n8n

n8n writes plain text, which works with dropdowns as long as the text **exactly matches** a dropdown option:
- Write `completed` not `Completed` or `COMPLETED`
- Write `generating` not `Generating`

If the text doesn't match, Google Sheets shows a warning but still accepts the value.

#### Step 3: Add Conditional Formatting (Colors)

In Google Sheets, add conditional formatting for the Status column:

1. Select column D (Status column)
2. **Format** → **Conditional formatting**
3. Add these rules:

**Rule 1: Completed (Green)**
- Format cells if: Text is exactly `completed`
- Formatting style: Green background (#b7e1cd)

**Rule 2: Generating (Yellow)**
- Format cells if: Text is exactly `generating`
- Formatting style: Yellow background (#fff2cc)

**Rule 3: Failed (Red)**
- Format cells if: Text is exactly `failed`
- Formatting style: Red background (#f4c7c3)

**Rule 4: Pending (Gray)**
- Format cells if: Text is exactly `pending`
- Formatting style: Gray background (#d9d9d9)

### Checkboxes for Social Media Platforms

Make columns F-I into checkboxes:
1. Select columns F through I (under YouTube, TikTok, etc.)
2. **Insert** → **Checkbox**
3. Check off each platform after you upload manually

### Video Link Column

The video link points to your local Docker backend. Format options:

**Option 1: Clickable HTTP Link (works in browser)**
```
http://localhost:8000/static/shorts/{project_id}.mp4
```

**Option 2: Local File Path (for reference only)**
Since Docker stores files in a volume, the actual Windows path is:
```
D:\User\Jansen\Self Study\2025 - 12 - DECEMBER\Faceless Youtube Factory\backend\static\shorts\{project_id}.mp4
```

To make it clickable in Google Sheets:
1. In the Video Link cell, use this formula:
```
=HYPERLINK("http://localhost:8000/static/shorts/"&C2&".mp4", "Open Video")
```
(Where C2 is the Project ID cell)

### Example Sheet Layout

| Date | Topic | Project ID | Status | Video Link | YouTube | TikTok | Instagram | Facebook |
|------|-------|------------|--------|------------|---------|--------|-----------|----------|
| 2025-01-05 | Why you forget names | abc123 | completed | [Open Video](#) | ☑ | ☐ | ☐ | ☐ |
| 2025-01-05 | Signs of high IQ | def456 | generating | - | ☐ | ☐ | ☐ | ☐ |

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

