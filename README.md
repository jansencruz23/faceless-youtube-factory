# Faceless YouTube Factory

AI-powered video generation and multi-platform upload automation. Create engaging short-form videos from text prompts with AI-generated scripts, text-to-speech voices, background music, and automated publishing.

## Features

### Video Generation
- **AI Script Generation** - Groq's LLama 3.3 generates engaging multi-speaker video scripts
- **Intelligent Voice Casting** - AI selects from 100+ Microsoft Edge TTS voices based on character
- **Voice Customization** - Adjust pitch and speed per character
- **Vertical Video (Shorts/Reels)** - 9:16 format with background video, music, and animated captions
- **Horizontal Video** - 16:9 format with per-scene AI images
- **Whisper-powered Captions** - Word-level accurate subtitles with pop-in animation

### Automation
- **n8n Workflow Integration** - Schedule automatic video generation every X hours
- **Automation API** - API key-authenticated endpoints for server-to-server automation
- **YouTube Auto-Upload** - One-click upload with AI-generated metadata
- **Real-time Updates** - WebSocket notifications for generation progress

### UI/UX
- **Modern Dark UI** - Glassmorphism design with Clerk authentication
- **Video Preview** - Download, copy URL, or open videos directly
- **Voice Casting Studio** - Visual voice assignment with audio preview

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│   PostgreSQL    │
│   (Next.js)     │◀────│   (FastAPI)     │◀────│    Database     │
│   Port 3000     │ WS  │   Port 8000     │     │   Port 5432     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                      │
         │              ┌───────▼───────┐
         │              │     n8n       │
         └─────────────▶│  Automation   │
                        │   Port 5678   │
                        └───────────────┘
```

**Pipeline:** Script Writer → Casting Director → Audio Generator → Video Composer → YouTube Uploader

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, LangGraph, Groq LLM, Edge-TTS, MoviePy, FFmpeg, Whisper |
| **Frontend** | Next.js 15, TypeScript, shadcn/ui, TanStack Query, Tailwind CSS, Clerk |
| **Database** | PostgreSQL, SQLAlchemy, asyncpg |
| **Automation** | n8n, Docker |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- NVIDIA GPU (optional, for faster Whisper)
- Groq API key ([console.groq.com](https://console.groq.com/keys))
- Clerk account ([clerk.com](https://clerk.com))
- Google Cloud project with YouTube Data API v3 (for YouTube upload)

### Setup

```bash
# Clone and configure
git clone https://github.com/yourusername/faceless-youtube-factory.git
cd faceless-youtube-factory
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up --build
```

Access:
- **App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **n8n Automation**: http://localhost:5678

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret key |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `TOKEN_ENCRYPTION_KEY` | Fernet key for OAuth tokens |
| `AUTOMATION_API_KEY` | Secret key for n8n automation |

## n8n Automation

Automate video generation on a schedule or on-demand.

### Automation API

```bash
# Create project and generate video
POST /api/v1/automation/generate
Header: X-API-Key: your-automation-key

{
  "topic": "5 mind-blowing psychology facts",
  "video_format": "vertical",
  "background_video": "preset:minecraft_parkour",
  "background_music": "preset:dreamland",
  "music_volume": 0.1,
  "enable_captions": true,
  "auto_upload": false
}
```

### Available Presets

| Type | Options |
|------|---------|
| **Background Video** | `preset:minecraft_parkour`, `preset:subway_surfers_neo` |
| **Background Music** | `preset:dreamland` |

See [N8N_AUTOMATION.md](docs/N8N_AUTOMATION.md) for full workflow setup.

## 📖 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/projects` | Create video project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/{id}` | Get project details |
| PUT | `/api/v1/projects/{id}/cast` | Update voice assignments |
| GET | `/api/v1/voices` | List available voices |
| POST | `/api/v1/automation/generate` | Create + auto-generate video |
| GET | `/api/v1/automation/status/{id}` | Get project status (for polling) |
| POST | `/api/v1/youtube/upload` | Upload to YouTube |

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── graph/           # LangGraph pipeline
│   │   │   └── nodes/       # Pipeline stages
│   │   ├── services/        # Video/audio generation
│   │   └── models/          # Database models
│   └── static/
│       └── presets/         # Background videos & music
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages
│       └── components/      # React components
├── docs/                    # Documentation
└── docker-compose.yml
```

## 📄 License

MIT
