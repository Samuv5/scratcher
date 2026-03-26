from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from api.job_scraper import get_jobs
from api.cv_optimizer import extract_cv_text, extract_job_from_url, extract_job_requirements, optimize_cv_with_job

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="Scratcher - CV Optimizer")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "client/dist/assets"), html=True), name="assets")

@app.get("/")
async def root():
    index_path = os.path.join(BASE_DIR, "client/dist/index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        return {"message": "Build the React app first: cd client && npm run build"}

@app.get("/api/jobs")
async def fetch_jobs(query: str = "Software Developer", location: str = "Remote", language: str = "es"):
    jobs = get_jobs(query, location, language)
    return {"jobs": jobs}

@app.post("/api/upload-cv")
async def upload_cv(cv_file: UploadFile = File(...)):
    try:
        pdf_content = await cv_file.read()
        cv_text = extract_cv_text(pdf_content)
        
        # Clean text for better detection
        import re
        clean_text = cv_text.replace('\f', ' ').replace('\n', ' ').replace('\r', ' ')
        
        skills = []
        common_skills = [
            # Programming and development
            "Python", "JavaScript", "TypeScript", "React", "React.js", "Node.js", "Node", "Java",
            "C++", "C#", "PHP", "Ruby", "Go", "Golang", "Rust", "Swift", "Kotlin",
            "SQL", "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite",
            "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "K8s", "Git", "GitHub", "GitLab",
            "HTML", "HTML5", "CSS", "CSS3", "SASS", "SCSS", "Tailwind", "Bootstrap", "REST", "REST API", "GraphQL", "Microservicios", "Microservices",
            "Machine Learning", "ML", "AI", "Artificial Intelligence", "Data Science", "Big Data", "TensorFlow", "PyTorch", "Pandas", "NumPy",
            "Agile", "Scrum", "Kanban", "DevOps", "CI/CD", "Linux", "Unix", "Security", "Cybersecurity",
            "Angular", "Vue", "Vue.js", "Svelte", "Next.js", "Nuxt", "Express", "FastAPI", "Django", "Flask", "Spring", "Spring Boot",
            "Deno", "Bun", "Webpack", "Vite", "Jest", "Mocha", "Cypress", "Selenium",
            "Figma", "Adobe", "Photoshop", "Illustrator", "UX", "UI",
            # Finance and accounting
            "Excel", "SAP", "QuickBooks", "Contabilidad", "Finanzas", "Análisis financiero",
            "Power BI", "Tableau", "Contable", "Auditoría", "Fiscal", "Tributario",
            "Costos", "Presupuesto", "Tesorería", "Bancario", "Bancario", "Financiero",
            # Risk management
            "Riesgos", "Riesgo Operativo", "Gestión de Riesgos", "Risk Management",
            "Compliance", "Cumplimiento", "Regulatorio", "Regulación", "Normatividad",
            "KYC", "AML", "Antilavado", "Due Diligence",
            "Control Interno", "Controles", "Auditoría Interna", "Auditoría Externa",
            "Operaciones", "Operativo", "Procesos", "Mejora de Procesos",
            "KPI", "Indicadores", "Métricas", "Reportes", "Reporting",
            "Stress Testing", "Pruebas de Estrés", "Escenarios",
            # Banking and advanced finance
            "Banca", "Banquero", "Fintech", "Crédito", "Préstamos",
            "Inversiones", "Portafolio", "Activos", "Pasivos",
            "Contabilidad", "NIIF", "IFRS", "US GAAP",
            "Tesorería", "Liquidez", "Capital", "Basel", "Basilea",
            # Soft skills
            "Liderazgo", "Gestión", "Management", "Equipo", "Team",
            "Análisis", "Analytical", "Problem Solving", "Resolución de Problemas",
            "Comunicación", "Communication", "Presentaciones", "Negociación",
            "Proyecto", "Project Management", "PMP",
            "Software", "Herramientas", "Sistemas", "Plataformas",
            "Word", "PowerPoint", "Outlook", "Teams", "Zoom"
        ]
        
        cv_text_upper = clean_text.upper()
        for skill in common_skills:
            # Use regex to find whole words
            pattern = r'\b' + re.escape(skill.upper()) + r'\b'
            if re.search(pattern, cv_text_upper):
                skills.append(skill)
        
        return {
            "success": True,
            "cv_text": cv_text,
            "skills": list(dict.fromkeys(skills))[:15]  # Remove duplicates, keep order
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/analyze-job")
async def analyze_job(url: str = Form(...)):
    try:
        job_text = extract_job_from_url(url)
        if "Error" in job_text:
            return {"success": False, "error": job_text}
        
        requirements = extract_job_requirements(job_text)
        return {
            "success": True,
            "requirements": requirements,
            "job_text": job_text[:2000]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/analyze-job-text")
async def analyze_job_text(job_text: str = Form(...)):
    try:
        if not job_text.strip():
            return {"success": False, "error": "Text cannot be empty"}
        
        requirements = extract_job_requirements(job_text)
        return {
            "success": True,
            "requirements": requirements,
            "job_text": job_text[:2000]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/optimize")
async def optimize(
    cv_file: UploadFile = File(...),
    job_url: str = Form(""),
    job_text: str = Form(""),
    job_title: str = Form("Puesto")
):
    try:
        pdf_content = await cv_file.read()
        cv_text = extract_cv_text(pdf_content)
        
        # Use direct text if provided, otherwise extract from URL
        if job_text.strip():
            job_source = job_text
        elif job_url.strip() and job_url.startswith('http'):
            job_source = extract_job_from_url(job_url)
        else:
            job_source = job_text or job_url or "Job Position"
        
        requirements = extract_job_requirements(job_source)
        optimized_cv = optimize_cv_with_job(cv_text, requirements, job_title)
        
        return {
            "success": True,
            "optimized_cv": optimized_cv,
            "requirements": requirements
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/optimize-text")
async def optimize_text(
    cv_text: str = Form(...),
    job_text: str = Form(...),
    job_title: str = Form(...)
):
    try:
        requirements = extract_job_requirements(job_text)
        optimized_cv = optimize_cv_with_job(cv_text, requirements, job_title)
        
        return {
            "success": True,
            "optimized_cv": optimized_cv,
            "requirements": requirements
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
