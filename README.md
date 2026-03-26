# Scratcher - CV Optimizer

Scratcher is a web application designed to optimize resumes (CVs) and search for jobs automatically. It uses natural language processing (NLP) and web scraping techniques to analyze job requirements and suggest improvements to the user's CV.

## Features

- **CV Optimization**: Analyzes CV content and adapts it to specific job vacancies.
- **Job Search**: Extracts job offers from various sources based on keywords and location.
- **Modern Web Interface**: Built with React and Vite on the frontend, and FastAPI on the backend.
- **Text Extraction**: Supports multiple file formats (PDF, DOCX, etc.) for the CV.
- **AI-Powered**: Uses local AI models via LM Studio or external APIs for intelligent CV optimization.

## Project Structure

```
.
├── api/                  # Backend modules (FastAPI)
│   ├── ai_prompts.py     # AI optimization prompts
│   ├── cv_optimizer.py   # CV optimization logic
│   ├── job_scraper.py    # Job offer web scraping
│   └── __init__.py
├── client/               # Frontend (React + Vite)
│   ├── src/              # React source code
│   ├── public/           # Static assets
│   ├── package.json      # Node.js dependencies
│   └── vite.config.js    # Vite configuration
├── static/               # Static files served by FastAPI
│   ├── index.html
│   ├── script.js
│   └── style.css
├── main.py               # FastAPI entry point
├── run.sh                # Server execution script
├── start.sh              # Alternative startup script
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Prerequisites

- Python 3.10+
- Node.js 16+ (for the frontend)
- npm or yarn
- LM Studio (for local AI) OR an AI API key (OpenAI, etc.)

## AI Configuration

### Option 1: Local AI with LM Studio (Recommended)
1. Install [LM Studio](https://lmstudio.ai/)
2. Download a model (e.g., Nemotron-3-Nano-4B or any GGUF model)
3. Start the local server in LM Studio (usually at `http://localhost:1234`)
4. The application will automatically connect to `http://localhost:1234/v1/chat/completions`

### Option 2: External AI API
1. Get an API key from OpenAI, Anthropic, or another provider
2. Set the environment variable:
   ```bash
   export AI_API_KEY="your-api-key-here"
   export AI_API_URL="https://api.openai.com/v1/chat/completions"
   ```
3. Modify `api/cv_optimizer.py` to use the external API endpoint

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd scratcher
   ```

2. **Set up the backend**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**:
   ```bash
   cd client
   npm install
   npm run build
   ```

## Usage

1. **Start the server**:
   ```bash
   # From the project root
   python main.py
   # Or using the script
   ./run.sh
   ```

2. **Access the application**:
   Open your browser and visit `http://localhost:8000`.

## API Endpoints

- `GET /`: Serves the React application.
- `GET /api/jobs?query=...&location=...&language=...`: Gets jobs based on parameters.
- `POST /api/upload-cv`: Uploads a CV for optimization.
- `POST /api/optimize-text`: Optimizes CV text against job requirements.

## Main Dependencies

### Backend (Python)
- FastAPI
- uvicorn
- requests
- beautifulsoup4
- pdfminer.six (for PDF extraction)

### Frontend (JavaScript)
- React
- Vite
- Axios (for HTTP requests)

## License

This project is under the MIT License.

## Contributing

Contributions are welcome. Please open an issue or pull request in the repository.