# Scratcher - CV Optimizer

Scratcher optimizes resumes (CVs) for real job openings. Upload your CV, paste a job link, and get an adapted version highlighting your relevant skills — with or without AI.

## Features

- **Real job scrapers**: Fetches listings from Indeed, LinkedIn, and Computrabajo based on your filters.
- **Smart optimization**: Tries local AI first (LM Studio); falls back to keyword matching if unavailable.
- **3 visual templates**: Modern, Classic, and Minimal — pick before you optimize.
- **Inline editor**: Modify the optimized CV before downloading.
- **Diff view**: Side-by-side comparison of original vs optimized CV.
- **Multi-format export**: PDF, HTML (with visual template), and DOCX (Word).
- **SQLite persistence**: History of uploaded CVs, analyzed jobs, and optimizations.
- **SSE streaming**: Step-by-step progress bar while processing.
- **Dark/Light theme**: Persisted in localStorage.
- **Offline mode**: Works fully without AI, with an indicator badge.
- **Tests**: pytest suite (backend) + vitest (frontend).

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
- Node.js 18+ (for the frontend)
- npm

## Quick Start

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

# Start
python main.py
# Open http://localhost:8000
```

## AI Configuration

> The app works **without AI** using keyword matching. AI is optional.

### LM Studio (local, recommended)
1. Install [LM Studio](https://lmstudio.ai/)
2. Download any GGUF model
3. Start the local server at `http://localhost:1234`
4. The app connects automatically

## Development (hot reload)

```bash
# Terminal 1 — Backend
python main.py

# Terminal 2 — Frontend (proxied to :8000)
cd client
npm run dev
# Open http://localhost:5173
```

## Tests

```bash
# Backend
pytest tests/ -v

# Frontend
cd client && npm test
```

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/health` | Health check + `ai_available` |
| GET | `/api/jobs` | Scrape job listings (Indeed, LinkedIn, Computrabajo) |
| GET | `/api/jobs/history` | Recently analyzed jobs |
| GET | `/api/cvs` | Uploaded CVs history |
| GET | `/api/templates` | Available CV templates |
| GET | `/api/optimizations` | Optimization history |
| POST | `/api/upload-cv` | Upload CV + detect skills |
| POST | `/api/analyze-job` | Analyze job from URL |
| POST | `/api/analyze-job-text` | Analyze job from text |
| POST | `/api/optimize` | Optimize CV (file upload) |
| POST | `/api/optimize-text` | Optimize CV (direct text) |
| POST | `/api/optimize-stream` | Optimize with SSE progress |
| POST | `/api/export/html` | Export CV to HTML |
| POST | `/api/export/docx` | Export CV to DOCX |
| POST | `/api/diff` | Diff original vs optimized |
| GET/POST | `/api/settings/{key}` | Read/write settings |

## Dependencies

### Backend
`fastapi` · `uvicorn` · `requests` · `beautifulsoup4` · `lxml` · `pdfminer.six` · `python-docx` · `python-multipart` · `sse-starlette` · `loguru` · `pytest` · `httpx`

### Frontend
`react` · `react-dom` · `jspdf` · `vite` · `vitest` · `jsdom`

## License

GNU GPLv3 with additional terms.
