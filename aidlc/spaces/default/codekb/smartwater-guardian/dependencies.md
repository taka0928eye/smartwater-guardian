# SmartWater Guardian - 依存関係

## Internal Dependencies (Cross-Module)

### Import Graph

```
main.py (Bootstrap)
  ├─ FastAPI()
  ├─ routers/telemetry.py
  ├─ routers/alerts.py
  ├─ routers/sensors.py
  └─ dependencies.py

routers/telemetry.py
  ├─ FastAPI router
  ├─ schemas/telemetry.py (TelemetryRequest, TelemetryResponse)
  └─ store.py (get_store())

routers/alerts.py ★KEY MODULE
  ├─ FastAPI router
  ├─ schemas/alert.py (AlertSummary, AlertDetail, PipeInfo)
  ├─ services/ledger.py (find_pipe_by_hydrant, get_pipe_age)
  └─ store.py (get_store(), StoredTelemetry)

routers/sensors.py
  ├─ FastAPI router
  ├─ schemas/alert.py (SensorInfo, HydrantMaster, GeoJSON*)
  └─ store.py (get_store())

services/ledger.py (BE-4)
  ├─ schemas/pipe.py (PipeRecord)
  ├─ data/pipes.json (load via pathlib)
  └─ functools.lru_cache

services/audio.py (BE-3 stub)
  ├─ numpy (future FFT)
  ├─ scipy (future filters)
  └─ schemas/telemetry.py (AnalysisResult)

schemas/telemetry.py
  ├─ pydantic (BaseModel, validators, ConfigDict)
  └─ datetime

schemas/alert.py ★TYPE INCONSISTENCY TARGET
  ├─ pydantic
  ├─ schemas/telemetry.py (SeverityLevel, GeoLocation, AnalysisResult)
  └─ (no direct import of PipeMaterial - uses str instead)

schemas/pipe.py
  ├─ pydantic
  └─ typing (Literal)

store.py
  ├─ threading (Lock for concurrent access)
  ├─ dataclass
  ├─ schemas/telemetry.py (TelemetryRequest, TelemetryResponse, AnalysisResult)
  └─ (implicit: StoredTelemetry dict)

dependencies.py
  └─ FastAPI Depends()
```

### Detailed Call Paths

#### Alert Detail Retrieval (BE-6)
```
GET /api/v1/alerts/{telemetry_id}
  ↓
routers/alerts.py::get_alert_detail(telemetry_id)
  ├─ store.get(telemetry_id) → StoredTelemetry
  ├─ _build_pipe_info(record.hydrant_id)
  │   └─ services/ledger.py::find_pipe_by_hydrant(hydrant_id)
  │       └─ services/ledger.py::get_pipes() → list[PipeRecord]
  │           └─ data/pipes.json (loaded once, cached)
  ├─ services/ledger.py::get_pipe_age(pipe.installed_year) → int
  └─ Return: AlertDetail
     ├─ AlertSummary (base)
     ├─ location: GeoLocation
     ├─ analysis: AnalysisResult | None
     └─ pipe_info: PipeInfo ★ (material: str ← pipe.material: PipeMaterial)
```

#### Telemetry Reception (BE-1)
```
POST /api/v1/telemetry
  ↓
routers/telemetry.py::create_telemetry(request: TelemetryRequest)
  ├─ Pydantic validation (TelemetryRequest)
  │   ├─ audio_base64 decode check (validator)
  │   ├─ AwareDatetime timezone validation
  │   └─ GeoLocation range check
  └─ store.add_telemetry(request) → StoredTelemetry
      └─ (analysis: None for BE-1)
```

#### Pipe Lookup (BE-4)
```
services/ledger.py
  ├─ get_pipes() @lru_cache
  │   └─ _load_pipes(PIPES_PATH)
  │       ├─ path.read_text()
  │       ├─ json.loads()
  │       └─ [PipeRecord.model_validate(item) for item in data]
  │           └─ schemas/pipe.py validation
  │               ├─ pipe_id: str
  │               ├─ material: PipeMaterial ← Literal["ductile_iron", ...]
  │               ├─ diameter_mm: PipeDiameterMm ← Literal[75, 100, ...]
  │               ├─ route: GeoJSONLineString
  │               │   └─ validators: coordinate range check
  │               └─ hydrant_ids: list[str]
  │
  ├─ find_pipe_by_hydrant(hydrant_id: str) → PipeRecord|None
  │   └─ iterate get_pipes()[*].hydrant_ids
  │
  ├─ find_nearest_pipe(lat, lng) → PipeRecord|None
  │   └─ iterate get_pipes()[*].route.coordinates
  │       └─ _haversine_km(lat1, lng1, lat2, lng2) → distance
  │
  └─ get_pipe_age(installed_year: int) → int
      └─ REFERENCE_YEAR (2026) - installed_year
```

---

## External Dependencies

### Python Backend (pip packages)

#### Production Dependencies
```
FastAPI==0.104+          # Web framework (ASGI)
pydantic==2.x.x          # Data validation & serialization (strict mode)
numpy==1.26+             # Numerical arrays (FFT future use)
scipy==1.11+             # Scientific computing (signal processing future use)
uvicorn[standard]        # ASGI server (development/production)
python-multipart         # Form data handling
```

#### Development Dependencies
```
pytest==7.x.x            # Test framework
pytest-cov==4.x.x        # Coverage measurement
ruff==0.1+               # Python linter (fast, ESLint-like)
black==23.x.x            # Code formatter (optional, Ruff subsumes)
mypy==1.x.x              # Static type checker (optional)
```

#### Version Strategy
- **FastAPI, Pydantic**: Pinned minor version (security updates only)
  - Reason: Type contracts are strict; major bumps risk incompatibility
- **NumPy, SciPy**: Pinned minor version
  - Reason: API stability, numerical precision
- **Pytest, Ruff**: Latest compatible
  - Reason: No runtime dependency; safe to upgrade

### Node.js Frontend (npm packages)

#### Core Dependencies
```json
{
  "react": "^18.0.0",
  "next": "latest",
  "typescript": "^5.0",
  "tailwindcss": "^3.x",
  "lucide-react": "latest",
  "leaflet": "1.9.4",
  "react-leaflet": "5.0.0",
  "recharts": "^2.x"
}
```

#### Dev Dependencies
```json
{
  "vitest": "latest",
  "eslint": "latest",
  "@types/react": "^18.x",
  "@types/node": "^18.x",
  "postcss": "^8.x",
  "autoprefixer": "^10.x"
}
```

#### Version Pinning
- **leaflet, react-leaflet**: Strict versions (1.9.4, 5.0.0)
  - Reason: Map rendering stability; minor bumps risk breaking changes
- **React, Next.js**: Caret ranges
  - Reason: Well-versioned; minor updates are backwards compatible
- **Tailwind, Lucide**: Latest with `^` caret
  - Reason: CSS/icon library; backward compatible

---

## Data Dependencies

### Master Data Files (JSON)

#### pipes.json (10 routes)
```
Location: backend/app/data/pipes.json
Format: Array of PipeRecord objects
Schema:
  - pipe_id: string
  - material: "ductile_iron" | "cast_iron" | "pvc" | "steel"
  - diameter_mm: 75 | 100 | 150 | 200
  - installed_year: 1965-2015
  - burial_depth_m: > 0
  - route: GeoJSON LineString [lng, lat]
  - hydrant_ids: string[]

Usage:
  - ledger.get_pipes() loads once, cached
  - find_pipe_by_hydrant() searches hydrant_ids
  - find_nearest_pipe() iterates coordinates

Validation:
  - Pydantic PipeRecord.model_validate()
  - GeoJSONLineString coordinate checks
```

#### hydrants.json (consumer hydrant list)
```
Location: backend/app/data/hydrants.json
Format: Array of HydrantMaster objects
Schema:
  - hydrant_id: string
  - sensor_id: string
  - name: string (descriptive)
  - latitude: -90 to 90
  - longitude: -180 to 180
  - pipe_id: string (cross-ref to pipes.json)

Usage:
  - sensors.py lists SensorInfo / GeoJSON Features
  - alerts.py uses hydrant_id to find pipe via ledger
  - FE displays on map

Validation:
  - Pydantic HydrantMaster.model_validate()
  - GeoLocation coordinate range checks
```

### Runtime Data (In-Memory)

#### StoredTelemetry (Store._records dict)
```
Structure:
  telemetry_id → StoredTelemetry
    ├─ sensor_id, hydrant_id
    ├─ received_at: datetime
    ├─ location: GeoLocation
    └─ analysis: AnalysisResult | None (BE-1: null)

Lifecycle:
  1. POST /api/v1/telemetry → store.add_telemetry()
  2. GET /api/v1/alerts/{id} → store.get(telemetry_id)
  3. Program exit → data lost (MVP scope)

Thread Safety:
  - threading.Lock protects concurrent access
```

---

## Cross-Layer Dependencies

### Module Dependency Matrix

| From | To | Type | Status |
|------|----|----|--------|
| alerts.py | ledger.py | Service | ✓ Used in _build_pipe_info() |
| alerts.py | store.py | Data | ✓ list_alerts(), get() |
| telemetry.py | store.py | Data | ✓ add_telemetry() |
| sensors.py | store.py | Data | ✓ implicit list via SensorInfo |
| ledger.py | pipes.json | File | ✓ Master data |
| routers/* | schemas/* | Validation | ✓ Request/Response contracts |
| audio.py | telemetry.py | Schema | ⊘ Future (AnalysisResult) |

### ★ Type Inconsistency Chain

```
pipes.json
  ├─ "material": "ductile_iron" (JSON string)
  └─ schemas/pipe.py
      └─ PipeMaterial = Literal["ductile_iron", ...]
         └─ PipeRecord.material: PipeMaterial (typed)
             └─ services/ledger.py
                 └─ find_pipe_by_hydrant() → PipeRecord
                     └─ routers/alerts.py
                         └─ _build_pipe_info()
                             └─ PipeInfo.material: str ★ (untyped)
                                 └─ AlertDetail.pipe_info
                                     └─ GET /api/v1/alerts/{id}

Problem: Type narrowing lost
- PipeRecord.material ∈ PipeMaterial (Literal, type-safe)
- PipeInfo.material: str (Any value, type-unsafe)
- Assignment: pipe_info.material = pipe.material ✓ compiles but untyped

Solution: Change PipeInfo.material: str → PipeMaterial
```

---

## Dependency Audit

### Unused Imports
- None identified in focused scan

### Circular Dependencies
- None detected

### Deprecated APIs
- ConfigDict(strict=True) is Pydantic v2 standard (not deprecated)
- AwareDatetime is Pydantic v2 preferred (replaces older custom validators)

### Security Advisories
- Monitor FastAPI, Pydantic monthly for CVEs
- NumPy/SciPy: Standard libraries with good maintenance

### Future Upgrade Blockers
- None known; Pydantic v2 is stable LTS target

