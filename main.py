import os
import re
import json
import asyncio
from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from api.job_scraper import get_jobs
from api.cv_optimizer import (
    extract_cv_text,
    extract_job_from_url,
    extract_job_requirements,
    optimize_cv_with_job,
)
from api.database import (
    init_db,
    save_cv,
    get_cv,
    get_cvs,
    save_job,
    get_job,
    get_recent_jobs,
    save_optimization,
    get_optimizations,
    get_optimization,
    get_setting,
    set_setting,
)
from api.templates import (
    render_cv_html,
    get_template_list,
    export_to_docx,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

# Configurar loguru
logger.add(
    os.path.join(DATA_DIR, "scratcher.log"),
    rotation="10 MB",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
)

app = FastAPI(title="Scratcher - CV Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "client/dist/assets"), html=True), name="assets")


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Scratcher started - Database initialized")


# --- Frontend ---

@app.get("/")
async def root():
    index_path = os.path.join(BASE_DIR, "client/dist/index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return {"message": "Build the React app first: cd client && npm run build"}


# --- Health ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Scratcher CV Optimizer", "ai_available": _check_ai()}


def _check_ai():
    try:
        import requests
        r = requests.get("http://localhost:1234/v1/models", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# --- Jobs ---

@app.get("/api/jobs")
async def fetch_jobs(
    query: str = Query("Software Developer"),
    location: str = Query("Remote"),
    language: str = Query("es"),
):
    logger.info(f"Fetching jobs: query='{query}', location='{location}', lang='{language}'")
    try:
        jobs = get_jobs(query, location, language)
        return {"jobs": jobs, "source": "live", "count": len(jobs)}
    except Exception as e:
        logger.error(f"Job fetch failed: {e}")
        return {"jobs": [], "source": "error", "error": str(e), "count": 0}


@app.get("/api/jobs/history")
async def job_history(limit: int = 20):
    return {"jobs": get_recent_jobs(limit)}


# --- CV Upload ---

@app.post("/api/upload-cv")
async def upload_cv(cv_file: UploadFile = File(...)):
    try:
        pdf_content = await cv_file.read()
        cv_text = extract_cv_text(pdf_content)

        clean_text = re.sub(r"[\f\n\r]", " ", cv_text)
        skills = _detect_skills(clean_text)

        cv_id = save_cv(cv_file.filename or "cv.pdf", cv_text, skills)
        logger.info(f"CV uploaded: id={cv_id}, skills={len(skills)}")

        return {
            "success": True,
            "cv_id": cv_id,
            "cv_text": cv_text,
            "skills": skills[:15],
        }
    except Exception as e:
        logger.error(f"CV upload failed: {e}")
        return {"success": False, "error": str(e)}


def _detect_skills(text):
    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "React.js", "Node.js", "Node", "Java",
        "C++", "C#", "PHP", "Ruby", "Go", "Golang", "Rust", "Swift", "Kotlin",
        "SQL", "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite",
        "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "K8s",
        "Git", "GitHub", "GitLab", "HTML", "HTML5", "CSS", "CSS3", "SASS", "SCSS",
        "Tailwind", "Bootstrap", "REST", "REST API", "GraphQL", "Microservicios", "Microservices",
        "Machine Learning", "ML", "AI", "Artificial Intelligence", "Data Science", "Big Data",
        "TensorFlow", "PyTorch", "Pandas", "NumPy", "Agile", "Scrum", "Kanban", "DevOps", "CI/CD",
        "Linux", "Unix", "Security", "Cybersecurity", "Angular", "Vue", "Vue.js", "Svelte",
        "Next.js", "Nuxt", "Express", "FastAPI", "Django", "Flask", "Spring", "Spring Boot",
        "Figma", "Adobe", "Excel", "SAP", "Power BI", "Tableau",
        "Liderazgo", "Gestión", "Management", "Comunicación", "Communication",
        "Project Management", "PMP", "KPI", "Reporting",
    ]
    found = []
    text_upper = text.upper()
    for skill in common_skills:
        pattern = r"\b" + re.escape(skill.upper()) + r"\b"
        if re.search(pattern, text_upper):
            found.append(skill)
    return list(dict.fromkeys(found))


# --- CV History ---

@app.get("/api/cvs")
async def list_cvs(limit: int = 10):
    return {"cvs": get_cvs(limit)}


@app.get("/api/cvs/{cv_id}")
async def get_cv_endpoint(cv_id: int):
    cv = get_cv(cv_id)
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


# --- Job Analysis ---

@app.post("/api/analyze-job")
async def analyze_job(url: str = Form(...)):
    try:
        job_text = extract_job_from_url(url)
        if "Error" in job_text:
            return {"success": False, "error": job_text}

        requirements = extract_job_requirements(job_text)
        job_id = save_job(
            title=requirements.get("title", "Position"),
            description=job_text[:2000],
            requirements=requirements,
            source="url",
            source_url=url,
        )
        logger.info(f"Job analyzed from URL: id={job_id}, title={requirements.get('title')}")

        return {
            "success": True,
            "job_id": job_id,
            "requirements": requirements,
            "job_text": job_text[:2000],
        }
    except Exception as e:
        logger.error(f"Job analysis failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/analyze-job-text")
async def analyze_job_text(job_text: str = Form(...)):
    try:
        if not job_text.strip():
            return {"success": False, "error": "Text cannot be empty"}

        requirements = extract_job_requirements(job_text)
        job_id = save_job(
            title=requirements.get("title", "Position"),
            description=job_text[:2000],
            requirements=requirements,
            source="text",
        )
        logger.info(f"Job analyzed from text: id={job_id}")

        return {
            "success": True,
            "job_id": job_id,
            "requirements": requirements,
            "job_text": job_text[:2000],
        }
    except Exception as e:
        logger.error(f"Job text analysis failed: {e}")
        return {"success": False, "error": str(e)}


# --- Optimize ---

@app.post("/api/optimize")
async def optimize(
    cv_file: UploadFile = File(...),
    job_url: str = Form(""),
    job_text: str = Form(""),
    job_title: str = Form("Position"),
    contact_info: str = Form(""),
    template: str = Form("modern"),
    cv_id: str = Form(""),
    job_id: str = Form(""),
):
    try:
        pdf_content = await cv_file.read()
        cv_text = extract_cv_text(pdf_content)

        if contact_info:
            cv_text = contact_info + "\n\n" + cv_text

        if job_text.strip():
            job_source = job_text
        elif job_url.strip() and job_url.startswith("http"):
            job_source = extract_job_from_url(job_url)
        else:
            job_source = job_text or job_url or "Job Position"

        requirements = extract_job_requirements(job_source)
        ai_used = bool(requirements.get("requirements"))

        optimized_cv = optimize_cv_with_job(cv_text, requirements, job_title)

        # Save to database
        db_cv_id = int(cv_id) if cv_id.isdigit() else save_cv("uploaded.pdf", cv_text)
        db_job_id = int(job_id) if job_id.isdigit() else save_job(
            title=job_title, description=job_source[:2000], requirements=requirements
        )
        opt_id = save_optimization(db_cv_id, db_job_id, job_title, cv_text, optimized_cv, template, int(ai_used))

        logger.info(f"CV optimized: opt_id={opt_id}, template={template}, ai={ai_used}")

        return {
            "success": True,
            "optimized_cv": optimized_cv,
            "requirements": requirements,
            "opt_id": opt_id,
            "ai_used": ai_used,
        }
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return {"success": False, "error": str(e)}


@app.post("/api/optimize-text")
async def optimize_text(
    cv_text: str = Form(...),
    job_text: str = Form(...),
    job_title: str = Form(...),
    contact_info: str = Form(""),
    template: str = Form("modern"),
):
    try:
        if contact_info:
            cv_text = contact_info + "\n\n" + cv_text

        requirements = extract_job_requirements(job_text)
        optimized_cv = optimize_cv_with_job(cv_text, requirements, job_title)

        return {
            "success": True,
            "optimized_cv": optimized_cv,
            "requirements": requirements,
        }
    except Exception as e:
        logger.error(f"Text optimization failed: {e}")
        return {"success": False, "error": str(e)}


# --- Optimize with SSE progress ---

@app.post("/api/optimize-stream")
async def optimize_stream(
    cv_file: UploadFile = File(...),
    job_url: str = Form(""),
    job_text: str = Form(""),
    job_title: str = Form("Position"),
    contact_info: str = Form(""),
    template: str = Form("modern"),
    cv_id: str = Form(""),
    job_id: str = Form(""),
):
    pdf_content = await cv_file.read()

    async def event_generator():
        yield {"event": "progress", "data": "Reading PDF..."}
        await asyncio.sleep(0.3)
        cv_text = extract_cv_text(pdf_content)

        if contact_info:
            cv_text = contact_info + "\n\n" + cv_text

        yield {"event": "progress", "data": "Analyzing job requirements..."}
        await asyncio.sleep(0.3)

        if job_text.strip():
            job_source = job_text
        elif job_url.strip() and job_url.startswith("http"):
            job_source = extract_job_from_url(job_url)
        else:
            job_source = job_text or job_url or "Job Position"

        requirements = extract_job_requirements(job_source)
        ai_used = bool(requirements.get("requirements"))

        yield {"event": "progress", "data": "Optimizing CV..."}
        await asyncio.sleep(0.3)

        optimized_cv = optimize_cv_with_job(cv_text, requirements, job_title)

        # Save to database
        db_cv_id = int(cv_id) if cv_id.isdigit() else save_cv("uploaded.pdf", cv_text)
        db_job_id = int(job_id) if job_id.isdigit() else save_job(
            title=job_title, description=job_source[:2000], requirements=requirements
        )
        opt_id = save_optimization(db_cv_id, db_job_id, job_title, cv_text, optimized_cv, template, int(ai_used))

        yield {
            "event": "result",
            "data": json.dumps({
                "optimized_cv": optimized_cv,
                "requirements": requirements,
                "opt_id": opt_id,
                "ai_used": ai_used,
            }),
        }

    return EventSourceResponse(event_generator())


# --- Optimizations History ---

@app.get("/api/optimizations")
async def list_optimizations(limit: int = 20):
    return {"optimizations": get_optimizations(limit)}


@app.get("/api/optimizations/{opt_id}")
async def get_optimization_endpoint(opt_id: int):
    opt = get_optimization(opt_id)
    if not opt:
        raise HTTPException(status_code=404, detail="Optimization not found")
    return opt


# --- Templates ---

@app.get("/api/templates")
async def templates_list():
    return {"templates": get_template_list()}


# --- Export ---

@app.post("/api/export/html")
async def export_html(cv_text: str = Form(...), template: str = Form("modern")):
    html = render_cv_html(cv_text, template)
    return HTMLResponse(html)


@app.post("/api/export/docx")
async def export_docx_endpoint(cv_text: str = Form(...), template: str = Form("modern")):
    try:
        buf = export_to_docx(cv_text, template)
        return Response(
            content=buf.read(),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=cv_optimized.docx"},
        )
    except Exception as e:
        logger.error(f"DOCX export failed: {e}")
        return {"success": False, "error": str(e)}


# --- Diff ---

@app.post("/api/diff")
async def diff_cv(original: str = Form(...), optimized: str = Form(...)):
    """Return a simple line-by-line diff indication."""
    orig_lines = original.split("\n")
    opt_lines = optimized.split("\n")

    changes = []
    max_len = max(len(orig_lines), len(opt_lines))

    for i in range(max_len):
        orig = orig_lines[i] if i < len(orig_lines) else ""
        opt = opt_lines[i] if i < len(opt_lines) else ""
        if orig != opt:
            changes.append({
                "line": i + 1,
                "original": orig,
                "optimized": opt,
                "type": "modified" if orig and opt else ("added" if opt else "removed"),
            })

    return {
        "changes": changes[:100],
        "total_changes": len(changes),
        "original_length": len(orig_lines),
        "optimized_length": len(opt_lines),
    }


# --- Settings ---

@app.get("/api/settings/{key}")
async def get_setting_endpoint(key: str):
    return {"key": key, "value": get_setting(key)}


@app.post("/api/settings/{key}")
async def set_setting_endpoint(key: str, value: str = Form(...)):
    set_setting(key, value)
    return {"success": True}


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
