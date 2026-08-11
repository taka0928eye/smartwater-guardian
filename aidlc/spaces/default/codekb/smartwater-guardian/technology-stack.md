# SmartWater Guardian - テクノロジースタック

## Backend Stack

### Framework & Server
| Component | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.104+ | Web framework (ASGI) |
| **Uvicorn** | Latest | ASGI server (development: `uvicorn main:app --reload --port 8000`) |
| **Python** | 3.11+ | Language |

### Data Validation & Serialization
| Component | Version | Purpose |
|-----------|---------|---------|
| **Pydantic** | v2.x | Data validation, serialization (strict mode enforced) |
| **typing** | Built-in | Type hints (from `__future__ import annotations`) |

### Signal Processing (BE-3)
| Component | Version | Purpose |
|-----------|---------|---------|
| **NumPy** | Latest | FFT計算、配列操作 |
| **SciPy** | Latest | 信号フィルタリング、周波数解析 |

### Testing & Quality
| Component | Version | Purpose |
|-----------|---------|---------|
| **pytest** | Latest | Unit/integration test framework |
| **pytest-cov** | Latest | Coverage report generation |
| **Ruff** | Latest | Python linter (ESLint equivalent) |

### Dependency Management
| Component | Version | Purpose |
|-----------|---------|---------|
| **pip** | Latest | Package manager |
| **requirements.txt** | - | Dependency pinning (production) |
| **pyproject.toml** | - | Build config, tool settings |

### Development Tools
| Component | Version | Purpose |
|-----------|---------|---------|
| **Git** | Latest | Version control |
| **GitHub Actions** | - | CI/CD pipeline |

---

## Frontend Stack

### Framework & Build
| Component | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | Latest | React framework (App Router) |
| **React** | 18+ | UI library |
| **TypeScript** | Latest | Type-safe JavaScript |
| **Node.js** | 18+ | Runtime |

### UI & Visualization
| Component | Version | Purpose |
|-----------|---------|---------|
| **Tailwind CSS** | Latest | Utility-first CSS framework |
| **Lucide React** | Latest | Icon library |
| **Leaflet** | 1.9.4 | Map library (core) |
| **react-leaflet** | 5.0.0 | React bindings for Leaflet |
| **Recharts** | Latest | Chart library (FE-4 spectrum visualization) |

### Testing & Quality
| Component | Version | Purpose |
|-----------|---------|---------|
| **Vitest** | Latest | Unit testing (Vite-native) |
| **ESLint** | Latest | JavaScript/TypeScript linter |

### Development Tools
| Component | Version | Purpose |
|-----------|---------|---------|
| **npm** / **bun** | Latest | Package manager |
| **Vite** | Latest | Build tool (Next.js内蔵) |

---

## Deployment & Infrastructure

### Development Environment
- **Local**: Python venv (`backend/venv/`), npm/bun for frontend
- **Database**: In-memory JSON (out-of-scope for production)

### Production Considerations (Out of Scope)
- Kubernetes / Docker (future)
- PostgreSQL / Cloud DB (future)
- Load balancer / API Gateway (future)
- CDN for static assets (future)

---

## Architecture-Specific Choices

### Why Python + FastAPI?

| Criterion | Choice | Reason |
|-----------|--------|--------|
| Backend Language | Python 3.11+ | NumPy/SciPy 信号処理の標準、開発速度 |
| Framework | FastAPI | Type-safe (Pydantic), async-ready, automatic API docs (Swagger) |
| ASGI Server | Uvicorn | FastAPI公式推奨、シンプル、development mode 対応 |

### Why Next.js + React?

| Criterion | Choice | Reason |
|-----------|--------|--------|
| Frontend Framework | Next.js | App Router、SSR対応、TypeScript統合 |
| UI Library | React | Component-driven、Leaflet/Recharts 統合エコシステム |
| Styling | Tailwind CSS | Utility-first、保守性、design consistency |
| Map Library | Leaflet + react-leaflet | 軽量、GeoJSON native対応、消火栓位置・エリア表示に最適 |

### Why Pydantic v2?

| Feature | Benefit |
|---------|---------|
| `strict=True` | IoT センサーデータの型厳密化（誤解釈防止） |
| `extra="forbid"` | 未知フィールド拒否（API破壊防止） |
| Built-in validators | Base64、座標範囲などの入力チェック内蔵 |
| OpenAPI integration | FastAPI が自動API docs生成（Swagger） |

---

## Version Pinning Strategy

### Backend (requirements.txt)
```
FastAPI==0.104.1
pydantic==2.x.x
numpy==1.26.0
scipy==1.11.0
pytest==7.x.x
pytest-cov==4.x.x
ruff==0.1.0
```
- **安定版**: マイナーバージョンまで固定
- **セキュリティ**: CVE発見時は即パッチ

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "next": "latest",
    "tailwindcss": "^3.x",
    "leaflet": "1.9.4",
    "react-leaflet": "5.0.0"
  }
}
```
- **Leaflet/react-leaflet**: 厳密版固定（互換性重要）
- **他**: 上位互換性想定で `^` (caret)

---

## Performance Characteristics

### Backend
| Metric | Target | Notes |
|--------|--------|-------|
| API Response | < 100ms | テレメトリ受信、アラート参照 |
| FFT処理 | < 500ms | BE-3（10.5秒音声） |
| メモリ | < 512MB | インメモリストア（デモ規模） |
| Concurrency | 10+ parallel | ThreadPoolExecutor + store.Lock |

### Frontend
| Metric | Target | Notes |
|--------|--------|-------|
| Initial Load | < 3s | Leaflet地図 + リアルタイムデータ |
| Map Render | < 1s | GeoJSON 50+ features |
| Interaction | < 200ms | ドロワー開閉、フィルタ |

---

## Security Considerations

### Input Validation (IoT Data)
- Pydantic strict mode enforced
- Base64 content validation
- Coordinate range checks
- Timezone-aware datetime parsing

### API Security (Out of Scope)
- ❌ Authentication/Authorization — CLAUDE.md §3
- ❌ Rate limiting — Future
- ❌ HTTPS enforcement — Future (development: HTTP only)
- ❌ API key management — Future

### Data Sensitivity
- ⚠️ Sensor telemetry: Location + timestamp + analysis data
  - Mitigation: Spatial/temporal aggregation in future privacy policies
- ⚠️ Master data: Hydrant locations (semi-public infrastructure)

---

## Build & Deployment Commands

### Backend
```bash
# Development
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python -m pytest --cov=app --cov-report=term-missing  # Run tests
python -m uvicorn main:app --reload --port 8000

# Production (future)
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Frontend
```bash
# Development
cd frontend
npm install  # or `bun install`
npm run dev

# Build
npm run build
npm run start

# Testing
npm run test
```

---

## Known Limitations & Caveats

| Issue | Impact | Resolution |
|-------|--------|-------------|
| No persistent DB | Data loss on restart | MVP scope; use PostgreSQL in production |
| Synchronous I/O | No async handlers | I/O wait minimal; acceptable for demo |
| No authentication | Anyone can access APIs | Out-of-scope; gate behind identity service |
| No rate limiting | Abuse potential | Out-of-scope; add API gateway in production |
| CORS open | Security risk | Development only; restrict in production |
| No HTTPS | Unencrypted transit | Development only; enforce in production |
| Haversine formula | Approximation (~0.5%) | Acceptable for demo; use PostGIS for precision |

---

## Future Technology Considerations

### Scaling Improvements
- **Async FastAPI handlers** — Move from sync to async (def → async def)
- **Message queue** — Kafka for telemetry streaming
- **Time-series DB** — InfluxDB for telemetry retention
- **Cache layer** — Redis for store acceleration

### Enhanced Analytics
- **Kubernetes** — Container orchestration
- **Prometheus** — Metrics collection
- **Grafana** — Observability dashboards
- **ELK Stack** — Log aggregation

### Map Features
- **Mapbox GL** — Advanced vector maps (Leaflet → Mapbox migration)
- **PostGIS** — Spatial database (hydrant.json → PostgreSQL)
- **Tile server** — Custom map tiles

