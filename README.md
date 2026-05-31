# Scratcher - CV Optimizer

Scratcher optimiza CVs para ofertas de trabajo reales. Subí tu CV, pegá el link de la oferta, y obtené una versión adaptada destacando tus skills relevantes — con o sin IA.

## Features

- **Scrapers reales**: Busca ofertas de Indeed, LinkedIn y Computrabajo según tus filtros.
- **Optimización inteligente**: Primero intenta con IA local (LM Studio); si no está disponible, usa matching por keywords.
- **3 plantillas visuales**: Modern, Classic y Minimal — elegís antes de optimizar.
- **Editor inline**: Modificá el CV optimizado antes de descargarlo.
- **Vista Diff**: Compará lado a lado el CV original vs el optimizado.
- **Exportación múltiple**: PDF, HTML (con template visual) y DOCX (Word).
- **Persistencia SQLite**: Historial de CVs subidos, trabajos analizados y optimizaciones.
- **Streaming con SSE**: Barra de progreso paso a paso mientras se procesa.
- **Tema oscuro/claro**: Persistente en localStorage.
- **Modo offline**: Funciona completo sin IA, con badge indicador.
- **Tests**: Suite de pytest (backend) + vitest (frontend).

## Project Structure

```
.
├── api/                      # Backend modules (FastAPI)
│   ├── __init__.py
│   ├── ai_prompts.py         # AI optimization prompts
│   ├── cv_optimizer.py       # CV optimization + PDF extraction
│   ├── database.py           # SQLite persistence layer
│   ├── job_scraper.py        # Real scrapers (Indeed, LinkedIn, Computrabajo)
│   └── templates.py          # CV HTML/DOCX templates
├── client/                   # Frontend (React + Vite)
│   ├── src/
│   │   ├── App.jsx           # Main component (step wizard)
│   │   ├── App.css           # Full dark/light theme styles
│   │   ├── App.test.jsx      # Vitest tests
│   │   ├── index.css         # Global reset
│   │   └── main.jsx          # Entry point
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── vitest.config.js
├── static/                   # Alternative vanilla-JS frontend
│   ├── index.html
│   ├── script.js
│   └── style.css
├── tests/                    # Backend tests
│   ├── __init__.py
│   └── test_backend.py       # 20+ pytest tests
├── main.py                   # FastAPI entry point (all routes)
├── data/                     # SQLite DB + logs (auto-created)
├── run.sh                    # Quick server start
├── start.sh                  # Full startup script
├── requirements.txt          # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (para el frontend)
- npm

## Instalación Rápida

```bash
git clone https://github.com/Samuv5/scratcher.git
cd scratcher

# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd client
npm install
npm run build
cd ..

# Iniciar
python main.py
# Abrir http://localhost:8000
```

## AI Configuration

> La app funciona **sin IA** usando matching por keywords. La IA es opcional.

### LM Studio (local, recomendado)
1. Instalar [LM Studio](https://lmstudio.ai/)
2. Descargar cualquier modelo GGUF
3. Iniciar el servidor local en `http://localhost:1234`
4. La app se conecta automáticamente

## Development (hot reload)

```bash
# Terminal 1 — Backend
python main.py

# Terminal 2 — Frontend (con proxy a :8000)
cd client
npm run dev
# Abrir http://localhost:5173
```

## Tests

```bash
# Backend
pytest tests/ -v

# Frontend
cd client && npm test
```

## API Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Health check + `ai_available` |
| GET | `/api/jobs` | Scrapea ofertas (Indeed, LinkedIn, Computrabajo) |
| GET | `/api/jobs/history` | Trabajos analizados recientemente |
| GET | `/api/cvs` | Historial de CVs subidos |
| GET | `/api/templates` | Lista de plantillas disponibles |
| GET | `/api/optimizations` | Historial de optimizaciones |
| POST | `/api/upload-cv` | Subir CV + detectar skills |
| POST | `/api/analyze-job` | Analizar oferta desde URL |
| POST | `/api/analyze-job-text` | Analizar oferta desde texto |
| POST | `/api/optimize` | Optimizar CV (archivo) |
| POST | `/api/optimize-text` | Optimizar CV (texto directo) |
| POST | `/api/optimize-stream` | Optimizar con SSE progress |
| POST | `/api/export/html` | Exportar CV a HTML |
| POST | `/api/export/docx` | Exportar CV a DOCX |
| POST | `/api/diff` | Diff original vs optimizado |
| GET/POST | `/api/settings/{key}` | Leer/escribir settings |

## Dependencias

### Backend
`fastapi` · `uvicorn` · `requests` · `beautifulsoup4` · `lxml` · `pdfminer.six` · `python-docx` · `python-multipart` · `sse-starlette` · `loguru` · `pytest` · `httpx`

### Frontend
`react` · `react-dom` · `jspdf` · `vite` · `vitest` · `jsdom`

## License

GNU GPLv3 with additional terms.
