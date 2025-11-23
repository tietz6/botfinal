# SALESBOT - Training System for Sales Managers

AI-powered training system for sales managers in the "На Счастье" project.

## 🎯 Overview

SALESBOT provides comprehensive training modules for sales managers and content creators in the "На Счастье" project:

### 🎓 Sales School (Training Modules)
- **Script Lab**: Interactive sales script practice with AI coach
- **Master Path**: Full sales cycle from greeting to final deal
- **Objections**: Handling customer objections with empathy
- **Upsell**: Cross-selling and upselling techniques
- **Arena**: Free-form dialog practice with different client types
- **Exam**: Final assessment with scoring
- **Sleeping Dragon**: Dialogue quality analysis and feedback

### 📚 Knowledge Base
- **Encyclopedia**: Comprehensive documentation with role-based access
- Training materials for managers and content creators
- Product documentation and sales guidelines

### 🎨 Content Creation Tools (for generators)
- **Song Generator**: AI-powered personalized song creation
- **Video Prompt Generator**: Scene-by-scene video timeline generation
- **Photo Animation**: Animation prompts for photo enhancement
- **Cases Analyzer**: Dialogue analysis with detailed feedback

### 🎭 Role-Based Access
- **Manager**: Sales training and client communication
- **Generator**: Content creation and production tools
- **Admin**: Full access to all modules

### 🎤 Voice Support
- Text and voice message training via Telegram
- Audio transcription and synthesis

## 🏗️ Architecture

### Backend (FastAPI)
- **Core Components**:
  - `core/state/`: SQLite-based state storage
  - `core/voice_gateway/v1/`: 🆕 Complete voice processing (ASR, LLM, TTS)
  - `router_autoload.py`: Automatic module discovery and registration

- **Training Modules** (all in `modules/`):
  - `dialog_memory/v1`: Session history and state management
  - `deepseek_persona/v1`: Brand voice ("На Счастье" style)
  - `training_scripts/v1`: 🆕 Script Lab - Interactive script practice
  - `master_path/v1`: Full sales cycle training
  - `objections/v1`: Objection handling training
  - `upsell/v1`: Upselling techniques
  - `arena/v1`: Free-form dialog practice
  - `exam/v1`: Final assessment
  - `sleeping_dragon/v1`: Dialogue analysis and coaching feedback

- **Knowledge Base**:
  - `encyclopedia/v1`: 🆕 Role-based documentation and training materials

- **Content Creation Modules**:
  - `song_generator/v1`: 🆕 AI-powered song text generation
  - `video_prompt_generator/v1`: 🆕 Video timeline and prompt generation
  - `photo_animation/v1`: 🆕 Photo animation prompt generation
  - `cases_analyzer/v1`: 🆕 Dialogue analysis with feedback

- **API Endpoints**:
  - `/api/public/v1/health`: Health check
  - `/api/public/v1/routes_summary`: All available routes
  - 🆕 **Voice API** (`/voice/v1/`):
    - `POST /asr`: Audio-to-text transcription (improved error handling)
    - `POST /tts`: Text-to-speech synthesis
    - `POST /chat/text`: Text-based LLM chat
    - `POST /chat/voice`: Voice-to-voice pipeline
  - 🆕 **Script Lab** (`/script_lab/`):
    - `POST /start/{session_id}`: Start interactive training session
    - `POST /turn/{session_id}`: Process manager's turn
    - `GET /result/{session_id}`: Get final training results
    - `POST /analyze`: Analyze a sales script (static analysis)
    - `GET /scenarios`: Get available training scenarios
  - 🆕 **Encyclopedia** (`/encyclopedia/v1/`):
    - `GET /pages?role={role}`: Get list of pages for role
    - `GET /page/{page_id}?role={role}`: Get specific page content
    - `POST /page/{page_id}/tts`: Generate TTS for page
  - 🆕 **Sleeping Dragon** (`/sleeping_dragon/v1/`):
    - `POST /analyze`: Analyze dialogue quality and get feedback
  - Each training module has:
    - `POST /<module>/start/{session_id}`: Start training session
    - `POST /<module>/turn/{session_id}`: Process manager's turn
    - `GET /<module>/snapshot/{session_id}`: Get session state
    - `GET /<module>/health`: Module health check

### Telegram Bot
- User-friendly interface for training
- Interactive menu with inline keyboards
- 🆕 **Role-based access**: Select role on first use (manager/generator/admin)
- 🆕 **Sales School**: Integrated training modules including Script Lab
- 🆕 **Knowledge Base**: Access to encyclopedia with role filtering
- 🆕 **Content Creation**: Song, video, and photo generation tools
- Real-time conversation with AI clients and coaches
- **Voice message support**: Send and receive voice messages
- **Text + Voice**: Works with both message types
- Session management per user

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in the root directory:

```env
# DeepSeek API Configuration (for LLM)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE_URL=https://api.deepseek.com/v1

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Voice API Configuration (for ASR and TTS)
VOICE_API_KEY=your_voice_api_key
VOICE_API_BASE_URL=https://your-voice-api.com

# Backend Configuration
BACKEND_URL=http://127.0.0.1:8080
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080

# Legacy LLM Configuration (for backward compatibility)
LLM_API_KEY=your_deepseek_api_key
LLM_API_URL=https://api.deepseek.com/v1/chat/completions
```

**Note**: The system works with fallback responses if API keys are not set, but for full functionality, configure all API keys.

### 3. Run Backend

```bash
python main.py
```

The backend will start on `http://localhost:8080`

Check health:
```bash
curl http://localhost:8080/api/public/v1/health
```

View all routes:
```bash
curl http://localhost:8080/api/public/v1/routes_summary
```

### 4. Run Telegram Bot (Optional)

In a separate terminal:

```bash
python simple_telegram_bot.py
```

## 📱 Using the Telegram Bot

### First Time Setup
1. Send `/start` to the bot
2. Choose your role:
   - 👨‍💼 **Manager** - For sales training and client communication
   - 🎨 **Generator** - For content creation tools
   - 👑 **Admin** - Full access to all features
3. Select from the main menu

### Main Menu Structure
- **🎓 Sales School** - Training modules for managers
  - 📖 Script Lab - Interactive script practice
  - 🎯 Master Path - Full sales cycle
  - 🛡️ Objections - Handle customer concerns
  - 💎 Upsell - Cross-selling techniques
  - 🎪 Arena - Free practice
  - 📝 Exam - Final assessment

- **📚 Knowledge Base** - Documentation (role-filtered)
  - Company introduction
  - Sales basics
  - Song creation process
  - Photo animation guide
  - Video production
  - Real cases and examples

- **🎨 Content Creation** (Generator/Admin only)
  - 🎵 Song Generator - Create personalized songs
  - 🎬 Video Prompts - Generate video timelines
  - 📸 Photo Animation - Animation prompts
  - 📊 Cases Analyzer - Dialogue analysis

- **🎯 Training Panel** - Quick access menu (via `/panel` command)
  - ✅ Тренировка - Access training modules
  - 👤 Клиент - Client practice (in development)
  - 🛡 Возражения - Objection handling
  - 📈 Апселл - Upselling techniques
  - 🎪 Арена - Free practice arena
  - 📝 Экзамен - Final examination
  - 📊 CRM - CRM system (coming soon)
  - ❌ Скрыть меню - Return to main menu

### Bot Commands
- `/start` - Initial setup and main menu
- `/panel` - Show training panel with quick access buttons
- `/master` - Quick start Master Path training
- `/result` - Get exam results (after completing exam)

### Training Sessions
- Send text messages or voice messages during training
- Bot responds as both client and coach
- Get real-time feedback on your technique
- Practice until you feel confident

### Content Generation
1. Select a content tool from the menu
2. Follow the prompts to provide input
3. Receive AI-generated content
4. Use "Create another" to generate more

## 📝 API Usage Examples

### Start Master Path Training

```bash
curl -X POST http://localhost:8080/master_path/start/session123?manager_id=user1
```

Response:
```json
{
  "success": true,
  "stage": "greeting",
  "coach_message": "Привет! 👋 Это тренировка полного цикла сделки...",
  "status": "active"
}
```

### Process Manager's Turn

```bash
curl -X POST http://localhost:8080/master_path/turn/session123?manager_id=user1 \
  -H "Content-Type: application/json" \
  -d '{"text": "Добрый день! Меня зовут София..."}'
```

Response:
```json
{
  "success": true,
  "stage": "greeting",
  "client_reply": "Здравствуйте! Интересно, расскажите подробнее.",
  "coach_tip": "Отличное начало! Добавь вопрос про получателя подарка.",
  "score": {"warmth": 8, "questions": 6, "clarity": 8}
}
```

### 🆕 Analyze Dialogue with Sleeping Dragon

```bash
curl -X POST http://localhost:8080/sleeping_dragon/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "history": [
      {"role": "assistant", "content": "Добрый день!"},
      {"role": "user", "content": "Привет"}
    ],
    "reply": "Расскажите, что вас интересует?"
  }'
```

Response:
```json
{
  "score": 5.6,
  "scores": {
    "warmth": 4.0,
    "questions": 3.0,
    "structure": 8.0,
    "no_pressure": 8.0,
    "active_listening": 5.0
  },
  "issues": ["Добавь больше тепла в общение"],
  "advice": "Хорошее начало! Добавь больше тепла...",
  "success": true
}
```

### 🆕 Text Chat with LLM

```bash
curl -X POST http://localhost:8080/voice/v1/chat/text \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "system", "content": "Ты - коуч"},
      {"role": "user", "content": "Как улучшить диалог?"}
    ]
  }'
```

### 🆕 Start Script Lab Training

**NEW PATH**: Script Lab interactive training is now available at `/script_lab/start` and `/script_lab/turn` endpoints.

```bash
curl -X POST http://localhost:8080/script_lab/start/session456 \
  -H "Content-Type: application/json" \
  -d '{"role": "manager", "topic": "song"}'
```

Response:
```json
{
  "success": true,
  "status": "active",
  "stage": "greeting",
  "coach_message": "Привет! Сегодня мы потренируем твой скрипт продажи...",
  "client_message": "Отлично! Мне нравится такой подход. Что дальше?",
  "hints": ["Начни с тёплого приветствия", "Узнай контекст"]
}
```

Process a turn:
```bash
curl -X POST http://localhost:8080/script_lab/turn/session456 \
  -H "Content-Type: application/json" \
  -d '{"text": "Здравствуйте! Как настроение?"}'
```

Response:
```json
{
  "success": true,
  "status": "active",
  "stage": "greeting",
  "client_reply": "Да, мне интересно! Расскажите, как это происходит?",
  "coach_tip": "Обрати внимание: важно не давить, а показать ценность через историю клиента.",
  "scores": {
    "warmth": 2.0,
    "clarity": 5.0,
    "questions": 3.0,
    "structure": 7.0,
    "pressure_free": 10
  },
  "is_final": false,
  "turn_count": 1
}
```

**Note**: The old `/training_scripts/v1/` endpoints are still available for backward compatibility, but new integrations should use `/script_lab/` paths.

### 🆕 Get Encyclopedia Pages

```bash
curl "http://localhost:8080/encyclopedia/v1/pages?role=manager"
```

Response:
```json
{
  "success": true,
  "total": 6,
  "pages": [
    {
      "id": "intro",
      "title": "Добро пожаловать в «На Счастье»",
      "description": "Знакомство с компанией, ценностями и миссией"
    },
    {
      "id": "sales_basics",
      "title": "Основы общения с клиентами",
      "description": "Принципы тёплого и эффективного общения"
    }
  ]
}
```

### 🆕 Generate Song

```bash
curl -X POST http://localhost:8080/song_generator/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "story": "Песня для жены на юбилей свадьбы. 10 лет вместе...",
    "style": "romantic",
    "mood": "love"
  }'
```

Response:
```json
{
  "success": true,
  "song": {
    "title": "Десять лет с тобой",
    "lyrics": "Куплет 1:\n...",
    "structure": {
      "intro": "...",
      "verse1": "...",
      "chorus": "..."
    }
  }
}
```

### 🆕 Set User Role

```bash
curl -X POST http://localhost:8080/api/public/v1/set_role \
  -H "Content-Type: application/json" \
  -d '{"user_id": "123456", "role": "manager"}'
```

Response:
```json
{
  "success": true,
  "user_id": "123456",
  "role": "manager",
  "message": "Role manager assigned to user 123456"
}
```

### Get Session Snapshot

```bash
curl http://localhost:8080/master_path/snapshot/session123?manager_id=user1
```

## 🎓 Training Modules

### 1. Master Path (`/master_path`)
Full sales cycle training with stages:
- **greeting**: First contact
- **story**: Collecting customer story
- **texts**: Preparing song texts
- **genre**: Genre selection
- **payment**: Payment discussion
- **demo**: Demo versions
- **final**: Final completion

### 2. Objections (`/objections`)
Practice handling:
- Price objections
- Trust issues
- "Need to think"
- "Maybe later"
- "Not needed"

### 3. Upsell (`/upsell`)
Scenarios:
- Pre-texts warmup
- Both demo versions
- 2→4 songs ladder
- Additional versions

### 4. Arena (`/arena`)
Free practice with client types:
- Calm and thoughtful
- Doubtful
- Price-focused
- Enthusiastic
- Busy

### 5. Exam (`/exam`)
Final assessment:
- Multiple rounds
- Combined scenarios
- Score: 0-100
- Grade: A/B/C/D

### 6. 🆕 Script Lab (`/training_scripts/v1`)
Interactive sales script practice:
- AI plays both client and coach roles
- Real-time feedback on technique
- Multiple topics: song, photo, cartoon, custom
- Stage-based progression (greeting → discovery → presentation → closing)
- Scoring across multiple criteria

### 7. 🆕 Sleeping Dragon (`/sleeping_dragon/v1`)
Dialogue quality analysis:
- Analyzes manager's dialogue quality
- 5 evaluation metrics (warmth, questions, structure, no pressure, active listening)
- Provides warm, constructive feedback
- Score: 0-10
- Identifies specific issues
- Suggests improvements

## 📚 Knowledge Base & Content Tools

### 🆕 Encyclopedia (`/encyclopedia/v1`)
Role-based documentation system:
- Company introduction and values
- Sales basics and communication principles
- Product guides (songs, photo animation, videos)
- Real-world case studies
- Access filtered by user role

### 🆕 Song Generator (`/song_generator/v1`)
AI-powered song creation:
- Multiple styles: romantic, rock, pop, acoustic, rap, jazz
- Emotional moods: love, support, celebration, gratitude, etc.
- Structured output: intro, verses, chorus, bridge
- Cover image prompts
- Voice performance notes

### 🆕 Video Prompt Generator (`/video_prompt_generator/v1`)
Timeline generation for AI video:
- Platform-specific prompts: Sora, VEO, Pika, Runway
- Scene-by-scene breakdown
- Emotion and visual style guidance
- Configurable chunk duration

### 🆕 Photo Animation (`/photo_animation/v1`)
Animation prompt generation:
- Photo analysis with recommendations
- Animation style suggestions
- Technical prompts for D-ID, Pika, Runway
- Emotion and action guidance

### 🆕 Cases Analyzer (`/cases_analyzer/v1`)
Dialogue analysis tool:
- Comprehensive dialogue evaluation
- Score across multiple criteria
- Identification of key moments
- Specific improvement recommendations

## 🎨 Brand Voice ("На Счастье")

The system uses a warm, empathetic communication style:
- Warm first contact, no pressure
- Lots of empathy and human phrasing
- No aggressive or dry phrases
- Transparent explanations

This is implemented in `modules/deepseek_persona/v1`.

## 🔧 Development

### Project Structure

```
botfinal/
├── main.py                 # FastAPI application
├── router_autoload.py      # Module auto-loader
├── simple_telegram_bot.py  # Telegram bot with voice support
├── .env                    # Environment configuration
├── core/
│   ├── state/             # SQLite storage
│   └── voice_gateway/v1/  # 🆕 Complete voice pipeline
│       ├── llm.py         # DeepSeek integration
│       ├── asr.py         # Speech-to-text
│       ├── tts.py         # Text-to-speech
│       └── pipeline.py    # Voice-to-voice
├── modules/
│   ├── dialog_memory/v1/          # Session management
│   ├── deepseek_persona/v1/       # Brand voice
│   │   └── persona.json           # Brand guidelines
│   ├── training_scripts/v1/       # 🆕 Script Lab
│   ├── master_path/v1/            # Full cycle training
│   ├── objections/v1/             # Objections
│   ├── upsell/v1/                 # Upselling
│   ├── arena/v1/                  # Free practice
│   ├── exam/v1/                   # Assessment
│   ├── sleeping_dragon/v1/        # Dialogue analysis
│   ├── encyclopedia/v1/           # 🆕 Knowledge base
│   ├── song_generator/v1/         # 🆕 Song creation
│   ├── video_prompt_generator/v1/ # 🆕 Video prompts
│   ├── photo_animation/v1/        # 🆕 Photo animation
│   └── cases_analyzer/v1/         # 🆕 Case analysis
└── api/
    ├── public/v1/                 # Public API endpoints
    │   └── roles management       # 🆕 User roles
    └── voice/v1/                  # Voice API
        └── routes.py              # ASR, TTS, chat
```

### Adding New Modules

1. Create module folder: `modules/my_module/v1/`
2. Create `__init__.py` with module logic
3. Create `routes.py` with FastAPI router
4. The module will be auto-loaded on startup

### Database

SQLite database (`salesbot.db`) stores:
- Session state
- Dialog history
- Scores and evaluations

Location: Root directory

## 🐛 Troubleshooting

### Backend won't start
- Check Python version (3.10+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8080 is available

### Telegram bot not responding
- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Ensure backend is running
- Check `BACKEND_URL` is correct

### No modules loaded
- Check `modules/` folder structure
- Each module needs `__init__.py` and `routes.py`
- Check backend logs for errors

### LLM not working
- System uses fallback mode if no external API
- Set `DEEPSEEK_API_KEY` and `DEEPSEEK_API_BASE_URL` for DeepSeek
- Fallback generates reasonable responses

### Voice messages not working
- Requires `VOICE_API_KEY` and `VOICE_API_BASE_URL`
- System shows error if API unavailable
- Bot can still work with text messages

## 📊 Monitoring

Health checks:
```bash
# Overall health
curl http://localhost:8080/api/public/v1/health

# Voice gateway
curl http://localhost:8080/voice/v1/health

# Module health
curl http://localhost:8080/master_path/health
curl http://localhost:8080/objections/health
curl http://localhost:8080/upsell/health
curl http://localhost:8080/arena/health
curl http://localhost:8080/exam/health
curl http://localhost:8080/sleeping_dragon/v1/health
```

## 🎤 Voice Features

The system now supports complete voice processing:

### Voice Gateway Components
- **ASR (Automatic Speech Recognition)**: Transcribe voice to text
- **LLM (Language Model)**: DeepSeek API for intelligent responses
- **TTS (Text-to-Speech)**: Synthesize text to voice
- **Pipeline**: Complete voice-to-voice processing

### Telegram Bot Voice Support
- Send voice messages during training
- Bot transcribes your voice to text
- Bot responds with both text and voice
- Seamless integration with all modules

### Voice API Endpoints
- `POST /voice/v1/asr`: Upload audio, get text
- `POST /voice/v1/tts`: Send text, get audio
- `POST /voice/v1/chat/text`: Text-based LLM chat
- `POST /voice/v1/chat/voice`: Voice-to-voice (ASR → LLM → TTS)

## 📄 License

Proprietary - "На Счастье" project

## 👥 Support

For issues or questions, contact the development team.
