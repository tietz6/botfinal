# SALESBOT - Training System for Sales Managers

AI-powered training system for sales managers in the "На Счастье" project.

## 🎯 Overview

SALESBOT provides comprehensive training modules for sales managers to practice:
- **Master Path**: Full sales cycle from greeting to final deal
- **Objections**: Handling customer objections with empathy
- **Upsell**: Cross-selling and upselling techniques
- **Arena**: Free-form dialog practice with different client types
- **Exam**: Final assessment with scoring

## 🏗️ Architecture

### Backend (FastAPI)
- **Core Components**:
  - `core/state/`: SQLite-based state storage
  - `core/voice_gateway/v1/`: LLM communication pipeline with fallback
  - `router_autoload.py`: Automatic module discovery and registration

- **Training Modules** (all in `modules/`):
  - `dialog_memory/v1`: Session history and state management
  - `deepseek_persona/v1`: Brand voice ("На Счастье" style)
  - `master_path/v1`: Full sales cycle training
  - `objections/v1`: Objection handling training
  - `upsell/v1`: Upselling techniques
  - `arena/v1`: Free-form dialog practice
  - `exam/v1`: Final assessment

- **API Endpoints**:
  - `/api/public/v1/health`: Health check
  - `/api/public/v1/routes_summary`: All available routes
  - Each module has:
    - `POST /<module>/start/{session_id}`: Start training session
    - `POST /<module>/turn/{session_id}`: Process manager's turn
    - `GET /<module>/snapshot/{session_id}`: Get session state
    - `GET /<module>/health`: Module health check

### Telegram Bot
- User-friendly interface for training
- Interactive menu with inline keyboards
- Real-time conversation with AI clients and coaches
- Session management per user

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Required for Telegram bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Backend configuration
BACKEND_URL=http://127.0.0.1:8080
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8080

# Optional: External LLM API (uses fallback if not set)
LLM_API_KEY=
LLM_API_URL=
```

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
├── simple_telegram_bot.py  # Telegram bot
├── core/
│   ├── state/             # SQLite storage
│   └── voice_gateway/v1/  # LLM pipeline
├── modules/
│   ├── dialog_memory/v1/  # Session management
│   ├── deepseek_persona/v1/ # Brand voice
│   ├── master_path/v1/    # Full cycle training
│   ├── objections/v1/     # Objections
│   ├── upsell/v1/         # Upselling
│   ├── arena/v1/          # Free practice
│   └── exam/v1/           # Assessment
└── api/
    └── public/v1/         # Public API endpoints
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
- Set `LLM_API_KEY` and `LLM_API_URL` for external LLM
- Fallback generates reasonable responses

## 📊 Monitoring

Health checks:
```bash
# Overall health
curl http://localhost:8080/api/public/v1/health

# Module health
curl http://localhost:8080/master_path/health
curl http://localhost:8080/objections/health
curl http://localhost:8080/upsell/health
curl http://localhost:8080/arena/health
curl http://localhost:8080/exam/health
```

## 📄 License

Proprietary - "На Счастье" project

## 👥 Support

For issues or questions, contact the development team.
