# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlphaPulse is an AI-powered cryptocurrency trading platform that integrates multiple AI models (Qiniu, Deepseek, SiliconFlow) with Binance Futures trading. The system generates trading recommendations through AI analysis of technical indicators, automates scheduled analysis, and tracks order profitability in real-time.

**Stack**: FastAPI + React + PostgreSQL + APScheduler + LangChain + Binance API

**Current Branch**: `ai_trader_v2` (multi-AI integration)
**Main Branch**: `master`

## Development Commands

### Backend (FastAPI)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest

# Run tests for specific module
pytest tests/test_ai_integration/
```

### Frontend (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Run development server (http://localhost:5173)
npm run dev

# Build for production
npm run build

# Lint TypeScript/React code
npm run lint

# Preview production build
npm run preview
```

### Database Setup

```bash
# Schema auto-initializes on first startup
# Or manually run:
psql -U username -d trading_db -f database/schema.sql
```

## Architecture Overview

### System Flow

```
Frontend (React)
    ↓ HTTP/WebSocket
API Router Layer (/api/*)
    ↓
Service Layer (OrderService, etc.)
    ↓
AI Manager → AIServiceFactory → AI Services (LangChain/Guiji)
    ↓
External APIs (Binance, AI providers, PostgreSQL)
```

### Core Components

**1. AI Integration (`ai_integration/`)**
- `AIManager`: Singleton managing all AI service instances
- `AIServiceFactory`: Factory pattern for creating service implementations
- `LangChainService`: OpenAI-compatible API wrapper (Qiniu, Deepseek)
- `GuijiService`: Silicon Flow API integration
- Config loaded from `ai_config.yaml` (runtime updates via API)

**2. API Routers (`app/api/routers/`)**
- `ai_router.py`: AI chat and trader analysis endpoints
- `order_router.py`: Trading order CRUD, dashboard, analytics
- `scheduler_router.py`: Job scheduling management
- `exchange_router.py`: Binance K-line data and symbols
- `realtime_router.py`: WebSocket streaming for prices/profits

**3. Schedulers (`app/scheduler/`)**
- `TradingScheduler`: APScheduler-based cron jobs for automated AI analysis
- `ProfitTracker`: Periodic profit tracking (30m, 1h, 2h, 4h intervals)

**4. Database (`app/db/`)**
- AsyncPG connection pool with singleton pattern
- Models: `AITradingOrder`, `OrderProfitTracking`, `RealtimeTrackingConfig`
- Schema: 3 tables with indexes, 1 analytics view (`order_statistics`)

**5. Exchange Integration (`exchanges/binance/`)**
- `BinanceFuturesClient`: Synchronous HTTP client for Binance Futures API
- `TechnicalIndicators`: 30+ TA-Lib indicators (MACD, RSI, Bollinger, MA, EMA, Stochastic, ATR, CCI, Williams %R, Ichimoku, SAR, VWAP, MFI, OBV, ADL, CMF, ADX, Volatility)

**6. Frontend (`frontend/src/`)**
- `App.tsx`: React Router setup
- Pages: `TradingOrders` (main), `Dashboard`, `SchedulerManager`, `AI`
- Components: Radix UI + Tailwind CSS + Lucide icons
- Charts: Lightweight Charts for candlestick visualization

### Key Design Patterns

- **Factory Pattern**: `AIServiceFactory` creates AI service instances
- **Singleton Pattern**: `AIManager`, database connection pool
- **Strategy Pattern**: Multiple AI service implementations
- **Repository Pattern**: `OrderService` abstracts data access
- **Middleware Pattern**: Request/response logging interceptors

## Configuration

### Critical Config Files

**`ai_integration/ai_config.yaml`** - Central configuration for:
- Database connection (host, port, credentials, pool settings)
- AI services (API keys, base URLs, models)
- Default service selection

**Security Warning**: This file contains hardcoded API keys and DB credentials. In production, migrate to environment variables or secrets manager.

**`.env.example`** - Template for environment variables (create `.env` for local overrides)

### Database Connection

Priority order:
1. Environment variables (`DATABASE_URL` or individual `DB_*` vars)
2. `ai_config.yaml` database section
3. Defaults from `app/core/config.py`

Connection pool initializes lazily on first query via `app/db/connection.py`.

## Data Models

### AITradingOrder (Primary Entity)
```python
{
    "id": int,
    "symbol": str,  # e.g., "BTCUSDT"
    "interval": str,  # e.g., "1h", "4h"
    "ai_model": str,
    "recommendation": "BUY" | "SELL" | "HOLD",
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "trend_status": str,  # 多头/空头/震荡
    "momentum": "bullish" | "bearish" | "neutral",
    "entry_price": Decimal,
    "entry_price_min": Decimal,  # suggested range
    "entry_price_max": Decimal,
    "stop_loss": Decimal,
    "stop_loss_percentage": Decimal,
    "target_t1": Decimal,  # profit target 1
    "target_t2": Decimal,  # profit target 2
    "target_t3": Decimal,  # profit target 3
    "position_size_percentage": Decimal,
    "status": "OPEN" | "STOP_LOSS" | "TAKE_PROFIT_T1" | "TAKE_PROFIT_T2" | "TAKE_PROFIT_T3" | "CLOSED",
    "analysis_summary": str,
    "indicator_alerts": str,
    "raw_analysis": dict,  # full AI response JSON
    "created_at": datetime,
    "closed_at": datetime | None,
    "closed_price": Decimal | None,
    "final_profit_percentage": Decimal | None
}
```

### OrderProfitTracking
Stores historical profit snapshots for each order at different tracking intervals.

## Common Development Scenarios

### Adding a New AI Service

1. Create service class in `ai_integration/services/` inheriting from `AIService`
2. Implement `chat_completion()` method
3. Add to `AIServiceFactory._service_mapping` in `factory.py`
4. Add configuration block to `ai_config.yaml`
5. Update `AIManager` to recognize new service

### Adding a New API Endpoint

1. Create router function in appropriate file under `app/api/routers/`
2. Include router in `app/main.py`
3. Add corresponding service logic if needed
4. Update frontend API calls

### Adding a Scheduled Job

1. Add job function in `app/scheduler/trading_scheduler.py`
2. Register job with cron expression using `scheduler.add_job()`
3. Start scheduler via `TradingScheduler.start()`
4. Manage via `/api/scheduler/*` endpoints

### Working with Technical Indicators

All indicators are calculated in `exchanges/binance/indicators.py` using TA-Lib. To add a new indicator:

1. Add calculation function in `TechnicalIndicators` class
2. Call function in `calculate_all()` method
3. Update return type annotations if needed

## Important Architectural Notes

### Async/Await Throughout
- All database operations use asyncpg (async)
- All API endpoints are async functions
- Scheduler uses AsyncIOScheduler
- HTTP clients use aiohttp/httpx

### Application Lifecycle

**Startup** (`app/main.py` → `@app.on_event("startup")`):
1. Initialize database connection pool
2. Run schema initialization
3. Start `ProfitTracker` scheduler
4. Start `TradingScheduler`

**Shutdown**:
1. Stop all schedulers
2. Close database connections

### Frontend-Backend Integration

- Backend serves frontend static files from `frontend/dist/`
- API endpoints prefixed with `/api/`
- CORS enabled for all origins (restrict in production)
- Middleware logs all requests/responses

### Error Handling

- API errors use `HTTPException` with appropriate status codes
- Database transactions rollback on error
- Scheduler jobs log failures but continue running
- Frontend displays error messages from API responses

## Testing

Run tests with pytest:
```bash
pytest                           # all tests
pytest tests/test_ai_integration/  # specific module
pytest -v                        # verbose output
pytest --cov=app                 # with coverage
```

Test files located in `tests/` directory.

## API Documentation

FastAPI auto-generates interactive docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Health check: http://localhost:8000/health

## Frontend Development

### Component Structure
- Uses functional components with React hooks
- TypeScript for type safety
- Tailwind CSS utility classes for styling
- Radix UI for accessible primitives
- Lucide React for icons

### State Management
- Local state with `useState`
- Side effects with `useEffect`
- No global state library (could add Context/Redux if needed)

### API Calls
- Axios for HTTP requests
- Base URL configured to backend API
- Error handling in try/catch blocks

## Notes for Future Development

- **Authentication**: No auth system currently implemented
- **API Keys**: Move from `ai_config.yaml` to secure secrets manager
- **Rate Limiting**: Add rate limiting middleware to protect API
- **Caching**: Consider Redis for K-line and AI response caching
- **WebSocket**: Real-time updates currently use polling (implement proper WebSocket)
- **Docker**: No containerization yet (consider adding Dockerfile + docker-compose)
- **CI/CD**: No automated testing/deployment pipeline
