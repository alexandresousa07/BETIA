# Football AI Analyst

Plataforma de inteligência artificial para análise de partidas de futebol em tempo real. Monitora estatísticas ao vivo, calcula probabilidades com múltiplos modelos de ML e gera oportunidades de apostas com score de confiança e explicações detalhadas.

**Este sistema NÃO realiza apostas** — apenas gera análises inteligentes.

## Stack

| Camada | Tecnologias |
|--------|-------------|
| Frontend | Next.js 15, React 19, TypeScript, TailwindCSS, Shadcn UI, React Query |
| Backend | Python 3.12, FastAPI, Pydantic, SQLAlchemy, Celery |
| ML | Scikit-Learn, XGBoost, Motor de Consenso (8 modelos) |
| Dados | API-Football, The Odds API |
| Infra | PostgreSQL (TimescaleDB), Redis, MLflow, Docker, NGINX |

## Início Rápido

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
```

Edite `.env` com suas chaves:
- `API_FOOTBALL_KEY` — [api-football.com](https://www.api-football.com/)
- `THE_ODDS_API_KEY` — [the-odds-api.com](https://the-odds-api.com/)

### 2. Subir com Docker

```bash
docker compose up -d
```

Serviços:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- MLflow: http://localhost:5000

### 3. Inicializar banco de dados

```bash
docker compose exec backend python scripts/init_db.py
docker compose exec backend python scripts/migrate_odds.py
docker compose exec backend python scripts/train_models.py --historical
```

> **Treinamento histórico** requer `API_FOOTBALL_KEY`. Sem chave, use `python scripts/train_models.py` (dados sintéticos).

### 4. Matching de Odds + Treinamento

**Matching automático** (API-Football ↔ The Odds API):
- Executado automaticamente ao sincronizar partidas ao vivo
- Celery task `match_odds` a cada 2 minutos
- Endpoint manual: `POST /api/v1/odds/match-all`

**Treinamento com dados históricos**:
```bash
# Via script
python scripts/train_models.py --historical --season 2024 --max-pages 5

# Via API
POST /api/v1/training/run
GET  /api/v1/training/status
```

### 5. Desenvolvimento local (sem Docker)

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python scripts/init_db.py
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Workers:**
```bash
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info
```

## Arquitetura

```
frontend/          → Dashboard Next.js (tema escuro)
backend/
  app/
    api/v1/        → REST API versionada
    core/          → Segurança, exceções, responses
    models/        → Entidades SQLAlchemy
    schemas/       → DTOs Pydantic
    repositories/  → Repository Pattern
    services/      → Service Pattern
    integrations/  → API-Football, The Odds API
    ml/            → Features, Predictors, Consenso
    workers/       → Celery tasks assíncronas
  tests/           → Unitários e integração
docs/              → Documentação arquitetural
monitoring/        → NGINX config
scripts/           → Utilitários
```

## Motor de IA

8 modelos alimentam um motor de consenso ponderado:

1. Estatístico
2. Bayesiano
3. Gradient Boosting
4. Random Forest
5. XGBoost
6. Rede Neural
7. LSTM (séries temporais)
8. Transformer (eventos)

Cada oportunidade inclui:
- Score de confiança (0–100)
- Nível (Baixa / Média / Alta / Muito Alta)
- Motivos baseados em estatísticas
- Explicação técnica completa
- Contribuição de cada modelo
- EV (valor esperado) quando odds disponíveis

## API

Base URL: `/api/v1`

| Endpoint | Descrição |
|----------|-----------|
| `GET /health` | Status do sistema |
| `POST /auth/register` | Registro |
| `POST /auth/login` | Login JWT |
| `GET /competitions` | Listar competições sincronizadas |
| `POST /competitions/sync` | Sincronizar todas as ligas da API-Football |
| `GET /competitions/countries` | Países disponíveis |
| `POST /competitions/{id}/sync-matches` | Partidas de uma competição |
| `GET /matches/live` | Partidas ao vivo |
| `GET /matches/{id}` | Detalhe da partida |
| `POST /matches/monitor` | Iniciar monitoramento |
| `GET /recommendations` | Entradas da IA |
| `GET /ai/models` | Modelos disponíveis |
| `POST /odds/match-all` | Matching odds para partidas ao vivo |
| `POST /odds/sync/{id}` | Sincronizar odds de uma partida |
| `GET /odds/status/{id}` | Status do matching e mercados |
| `POST /training/run` | Treinar modelos com dados históricos |
| `GET /training/status` | Métricas dos modelos treinados |
| `WS /ws/match/{id}` | WebSocket tempo real |

## Testes

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

## Licença

Projeto privado — Football AI Analyst © 2026
