# Arquitetura — Football AI Analyst

## Visão Geral

Sistema modular de análise de futebol em tempo real, projetado para escalabilidade e extensibilidade (novos esportes, modelos, mercados e APIs).

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend   │────▶│   NGINX      │────▶│  FastAPI Backend │
│  Next.js    │◀────│   Proxy      │◀────│  /api/v1         │
└─────────────┘     └──────────────┘     └────────┬────────┘
       │ WebSocket                                │
       └──────────────────────────────────────────┤
                                                  │
                    ┌─────────────────────────────┼──────────────────┐
                    │                             │                  │
              ┌─────▼─────┐  ┌──────────┐  ┌─────▼─────┐  ┌───────▼──────┐
              │ PostgreSQL │  │  Redis   │  │  Celery   │  │ Integrações  │
              │ TimescaleDB│  │  Cache   │  │  Workers  │  │ API-Football │
              └───────────┘  └──────────┘  └───────────┘  │ The Odds API │
                                                            └──────────────┘
```

## Decisões Arquiteturais

### 1. Clean Architecture + DDD

- **Controllers (API Routes)**: apenas roteamento e validação de entrada
- **Services**: lógica de negócio e orquestração
- **Repositories**: acesso a dados (Repository Pattern)
- **Integrations**: clientes HTTP para APIs externas
- **ML**: pipeline isolado de features → predictors → consenso

### 2. Fontes de Dados

| Fonte | Uso |
|-------|-----|
| API-Football | Partidas, stats ao vivo, eventos, H2H, **dados históricos para treinamento** |
| The Odds API | Odds de mercados (h2h, totals, spreads) |

Interfaces abstratas permitem trocar provedores sem refatoração.

### 2.1 Matching de Odds (API-Football ↔ The Odds API)

O `OddsMatcher` associa partidas a eventos de odds usando:

1. **Mapeamento de ligas** → `sport_key` da The Odds API (39 → `soccer_epl`, etc.)
2. **Normalização de nomes** — remove sufixos (FC, United), acentos, pontuação
3. **Similaridade fuzzy** — `SequenceMatcher` + Jaccard de tokens
4. **Proximidade de horário** — kickoff ±1h (peso 25%)
5. **Score mínimo** — 0.72 para confirmar match

Campos persistidos em `matches`: `odds_event_id`, `odds_sport_key`, `odds_match_confidence`.

Mercados mapeados para EV: `Over 2.5` → `over_2.5_goals`, etc.

### 2.2 Treinamento Histórico

Pipeline:

```
API-Football (fixtures FT + statistics)
    → HistoricalDataCollector
    → FeatureEngineer (29 features)
    → Labels (over_2.5, btts, corners...)
    → HistoricalTrainer (GBM, RF, XGBoost por mercado)
    → ml/artifacts/*.joblib + registry.json
    → TrainedModelPredictor no motor de consenso
```

Retreinamento automático: Celery Beat toda segunda às 03:00 UTC.

### 3. Motor de Consenso

Nenhuma decisão depende de um único modelo. O `ConsensusEngine`:

1. Executa 8 predictors em paralelo
2. Calcula média ponderada por peso do modelo
3. Avalia concordância entre modelos (agreement score)
4. Gera confiança final (0–100)
5. Filtra oportunidades abaixo do threshold (55%)
6. Produz explicação com motivos, prós, contras e EV

### 4. Pipeline de Dados ao Vivo

```
API-Football → Normalizer → Validator → Cache (Redis)
                              ↓
                         PostgreSQL (LiveStats, Events)
                              ↓
                    Feature Engineer → ML Predictors
                              ↓
                    Consensus Engine → Recommendations
                              ↓
                    WebSocket Broadcast + Alertas
```

Celery Beat executa:
- `sync_live_matches` — a cada 60s
- `update_monitored_matches` — a cada 30s

### 5. CQRS (Consultas Pesadas)

Leituras complexas (detalhe de partida com stats, events, odds, predictions, recommendations) usam queries otimizadas com `selectinload` no repository, separadas da lógica de escrita.

### 6. Segurança

- JWT + Refresh Token
- bcrypt para senhas
- Rate limiting (configurável)
- CORS restrito
- Validação Pydantic em todas as entradas
- SQLAlchemy ORM (proteção SQL Injection)

### 7. Extensibilidade

| Extensão | Como |
|----------|------|
| Novo esporte | Novo normalizer + feature engineer |
| Novo modelo | Implementar `BasePredictor`, registrar em `ALL_PREDICTORS` |
| Novo mercado | Adicionar em `MARKET_DEFINITIONS` |
| Nova API | Novo client em `integrations/` |
| Novo indicador | Extender `MatchFeatures` + normalizer |

## Modelo de Dados

Entidades principais: Users, Matches, Teams, Competitions, LiveStats, Events, Odds, Predictions, Recommendations, AIModels, TrainingHistory, Logs, Configurations, UserPreferences.

LiveStats usa TimescaleDB para séries temporais (momentum, xG por minuto).

## Frontend

Layout profissional com tema escuro:
- Sidebar de navegação
- Dashboard com KPIs
- Lista de partidas ao vivo
- Tela de partida: placar, stats, momentum chart, timeline, entradas, explicações
- Alertas de alta confiança
- Configurações de preferências

## Performance

- Redis cache (TTL 30–60s para partidas)
- WebSocket para push (sem polling)
- Celery workers paralelos
- Paginação nas listagens
- NGINX gzip + proxy

## Evolução Futura

1. Treinar modelos com dados históricos reais (substituir heurísticas)
2. LSTM/Transformer com PyTorch para séries temporais
3. Matching automático API-Football ↔ The Odds API
4. Rate limiting com Redis
5. Testes E2E com Playwright
6. Cobertura ≥ 80%
