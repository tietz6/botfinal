# SALESBOT Architecture - "На Счастье" Training System

## Overview

This is a modular training system for sales managers, content generators, and leadership of the "На Счастье" project. The system provides:

- **Encyclopedia**: Comprehensive knowledge base with role-based access
- **Interactive Training**: AI-powered sales script practice
- **Content Generation**: Song text, video prompts, and photo animation
- **Analytics**: Dialog analysis and performance tracking
- **Examinations**: Comprehensive skill assessment

## Architecture

### Core Infrastructure

#### `core/auth/`
Role-based access control system.

- **Roles**: `manager`, `generator`, `admin`
- **Storage**: SQLite via `core/state`
- **Integration**: FastAPI dependencies for endpoint protection

#### `core/llm_gateway/`
Unified interface to LLM services (Deepseek).

- Wraps existing `core/voice_gateway/v1/llm.py`
- High-level methods for different use cases:
  - `generate_client_reply()` - AI client simulation
  - `generate_coach_feedback()` - Training feedback
  - `generate_song_text()` - Song creation
  - `generate_video_prompts()` - Video timeline generation

#### `core/encyclopedia_engine/`
Content management for training materials.

- JSON-based page storage
- Role-based content filtering
- TTS-ready text extraction

### Modules

All modules follow the pattern: `modules/<module_name>/v1/routes.py`

#### 1. Encyclopedia (`/encyclopedia/v1`)
Training materials and documentation.

**Endpoints:**
- `GET /pages` - List available pages (role-filtered)
- `GET /page/{page_id}` - Get full page content
- `POST /page/{page_id}/tts` - Generate audio version

**Content Pages:**
- `intro.json` - Company introduction
- `sales_basics.json` - Sales fundamentals
- `song_process.json` - Song creation workflow
- `photo_animation.json` - Photo animation product
- `cartoons.json` - Cartoon video creation
- `cases.json` - Real-world case studies

#### 2. Training Scripts (`/training_scripts/v1`)
Interactive sales script practice.

**Features:**
- AI plays both client and coach roles
- Real-time feedback on technique
- Scoring across multiple criteria
- Stage progression (greeting → discovery → presentation → closing)

**Endpoints:**
- `POST /start/{session_id}` - Start training session
- `POST /turn/{session_id}` - Process manager's message
- `GET /result/{session_id}` - Get final evaluation

#### 3. Song Generator (`/song_generator/v1`)
AI-powered song text generation.

**Features:**
- Multiple styles (romantic, rock, pop, acoustic, rap, jazz)
- Emotional moods (love, support, celebration, gratitude, etc.)
- Structured output (intro, verses, chorus, bridge)
- Cover image prompts
- Voice performance notes

**Endpoints:**
- `POST /generate` - Generate song from story
- `GET /styles` - List available styles
- `GET /moods` - List emotional moods

#### 4. Video Prompt Generator (`/video_prompt_generator/v1`)
Timeline generation for AI video platforms.

**Features:**
- Platform-specific prompts (Sora, VEO, Pika, Runway)
- Scene-by-scene breakdown
- Emotion and visual style guidance
- Configurable chunk duration

**Endpoints:**
- `POST /from_song` - Generate timeline from song
- `GET /platforms` - List supported platforms
- `GET /styles` - List visual styles

#### 5. Photo Animation (`/photo_animation/v1`)
Analysis and prompts for photo animation.

**Features:**
- Photo analysis with recommendations
- Animation style suggestions
- Technical prompts for D-ID, Pika, Runway
- Emotion and action guidance

**Endpoints:**
- `POST /analyze` - Analyze photo for animation
- `POST /prompt` - Generate animation prompt
- `GET /styles` - List animation styles

#### 6. Cases Analyzer (`/cases_analyzer/v1`)
Dialog analysis and feedback.

**Features:**
- Comprehensive dialog evaluation
- Score across multiple criteria
- Identification of key moments
- Specific improvement recommendations

**Endpoints:**
- `POST /analyze` - Analyze completed dialog

#### 7. Exams (`/exams/v1`)
Comprehensive skill assessment.

**Features:**
- Multiple scenarios (song, photo, cartoon, full cycle)
- Round-based evaluation
- Final grading (A/B/C/D)
- Detailed performance breakdown

**Endpoints:**
- `POST /start/{session_id}` - Start exam
- `POST /turn/{session_id}` - Process exam turn
- `GET /result/{session_id}` - Get final results
- `GET /scenarios` - List available scenarios

### Public API (`/api/public/v1`)

User and system management.

**Endpoints:**
- `GET /health` - Health check
- `GET /routes_summary` - List all routes
- `POST /set_role` - Assign user role
- `GET /get_role/{user_id}` - Get user role
- `GET /roles` - List available roles

## Integration with Telegram Bot

The existing `simple_telegram_bot.py` integrates with all modules via HTTP API.

**User Flow:**
1. `/start` - User onboarding, role selection
2. Role assignment via `/api/public/v1/set_role`
3. Module selection from menu
4. Interactive training through module endpoints
5. Results and feedback

## Adding New Modules

To add a new module:

1. Create directory structure:
   ```
   modules/
     new_module/
       v1/
         __init__.py
         routes.py
   ```

2. Create `routes.py` with FastAPI router:
   ```python
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/new_module/v1", tags=["new-module"])
   
   @router.get("/health")
   async def health():
       return {"status": "healthy", "module": "new_module"}
   ```

3. Restart application - module auto-loads via `router_autoload.py`

## Environment Variables

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_token

# Backend
BACKEND_URL=http://127.0.0.1:8080
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080

# LLM (Deepseek)
DEEPSEEK_API_KEY=your_key
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1

# Voice Gateway (optional)
VOICE_API_KEY=your_key
VOICE_API_BASE_URL=your_url
```

## Running the System

### Start Backend
```bash
python main.py
```

### Start Telegram Bot
```bash
python simple_telegram_bot.py
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8080/api/public/v1/health

# List encyclopedia pages
curl http://localhost:8080/encyclopedia/v1/pages?role=manager

# Start training session
curl -X POST http://localhost:8080/training_scripts/v1/start/session123 \
  -H "Content-Type: application/json" \
  -d '{"role":"manager","topic":"song"}'
```

## Database

Uses SQLite (`salesbot.db`) for:
- User roles
- Session states
- Training progress
- Exam results

Database schema managed by `core/state/__init__.py`

## Security Notes

- Role-based access enforced at module level
- User authentication via headers (X-User-ID, X-Role)
- Production deployment should use proper JWT tokens
- Sensitive data (API keys) in environment variables only

## Development Guidelines

1. **Keep modules independent** - Each module should be self-contained
2. **Use core services** - Leverage `core/llm_gateway`, `core/auth`, `core/state`
3. **Follow naming conventions** - `modules/<name>/v1/routes.py`
4. **Add health checks** - Every module needs `/health` endpoint
5. **Document endpoints** - Use FastAPI docstrings
6. **Test thoroughly** - Verify both API and Telegram bot integration

## Future Enhancements

- [ ] JWT authentication
- [ ] User progress tracking dashboard
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Voice interface enhancement
- [ ] Team leaderboards
- [ ] Certificate generation for completed exams
