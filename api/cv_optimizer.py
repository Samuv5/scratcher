import io
import requests
import json
from pdfminer.high_level import extract_text as pdfminer_extract_text
from bs4 import BeautifulSoup

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def extract_text_from_pdf(pdf_bytes):
    try:
        text = pdfminer_extract_text(io.BytesIO(pdf_bytes))
        if not text.strip():
            return "Could not extract text from PDF."
        return text
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def extract_cv_text(pdf_bytes):
    return extract_text_from_pdf(pdf_bytes)

def extract_job_from_url(url):
    """Extract requirements from a job link"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = ' '.join(lines)
        
        return cleaned_text[:5000]
    except Exception as e:
        return f"Error extracting job: {str(e)}"

def clean_json(text):
    """Clean JSON by removing comments and fixing common errors"""
    # Remove JavaScript-style comments (// ...)
    import re
    # Remove single-line comments
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
    # Remove trailing commas before } or ]
    text = re.sub(r',(\s*[}\]])', r'\1', text)
    return text.strip()

def extract_job_requirements(job_text):
    """Extract requirements from job text - uses AI if available, otherwise keyword-based"""
    # Try AI extraction first
    ai_result = _extract_with_ai(job_text)
    if ai_result["requirements"]:
        return ai_result
    
    # Fallback: keyword-based extraction
    return _extract_with_keywords(job_text)

def _extract_with_ai(job_text):
    """Use AI to extract requirements from job text"""
    prompt = f"""Analyze this job offer and extract the information. Respond ONLY with valid JSON, no comments.

JOB OFFER:
{job_text[:15000]}

Respond with this exact JSON:
{{"title": "job title", "requirements": ["skill1", "skill2"], "experience": "years required", "languages": ["language1"], "responsibilities": ["responsibility1"]}}"""

    payload = {
        "model": "nvidia/nemotron-3-nano-4b",
        "messages": [
            {
                "role": "system",
                "content": "Respond ONLY with valid JSON. No explanations, no comments, no markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=90)
        result = response.json()
        
        if result.get("choices"):
            content = result["choices"][0].get("message", {}).get("content", "")
            
            # Extract JSON from code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            content = clean_json(content)
            
            try:
                parsed = json.loads(content)
                return {
                    "title": parsed.get("title", "Position"),
                    "requirements": parsed.get("requirements", []),
                    "experience": parsed.get("experience", "Not specified"),
                    "languages": parsed.get("languages", []),
                    "responsibilities": parsed.get("responsibilities", [])
                }
            except json.JSONDecodeError:
                pass
    except Exception:
        pass
    
    return {"title": "Position", "requirements": [], "experience": "Not specified", "languages": [], "responsibilities": []}

def _extract_with_keywords(job_text):
    """Fallback: extract requirements using keyword matching"""
    text_lower = job_text.lower()
    
    # Common requirement keywords
    skills_keywords = [
        "python", "javascript", "typescript", "react", "node.js", "node", "java",
        "c++", "c#", "php", "ruby", "go", "golang", "rust", "swift", "kotlin",
        "sql", "postgresql", "postgres", "mysql", "mongodb", "redis",
        "aws", "azure", "gcp", "docker", "kubernetes", "k8s", "git",
        "html", "css", "rest", "graphql", "microservices",
        "machine learning", "ai", "data science", "tensorflow", "pytorch",
        "agile", "scrum", "devops", "linux", "security", "ci/cd",
        "fastapi", "django", "flask", "spring", "angular", "vue",
        "excel", "power bi", "tableau", "sap",
        "leadership", "communication", "teamwork", "analytical"
    ]
    
    found = []
    for skill in skills_keywords:
        if skill in text_lower:
            found.append(skill.title())
    
    # Extract potential title (first line or line with common title words)
    title = "Position"
    lines = job_text.split('\n')
    for line in lines[:5]:
        line = line.strip()
        for prefix in ["job title:", "title:", "position:", "role:"]:
            if line.lower().startswith(prefix):
                title = line.split(":", 1)[1].strip()
                break
    
    # Extract experience info
    experience = "Not specified"
    import re
    exp_patterns = re.findall(r'(\d+)\+?\s*(?:years?|years\s+of\s+experience|experience)', job_text.lower())
    if exp_patterns:
        experience = f"{max(int(x) for x in exp_patterns)}+ years"
    
    # Return found skills as requirements
    return {
        "title": title,
        "requirements": found[:15],
        "experience": experience,
        "languages": [],
        "responsibilities": []
    }

def optimize_cv_with_job(cv_text, job_requirements, job_title):
    """Optimize CV based on user's REAL skills and job requirements"""
    # Prepare requirements text
    reqs_text = ""
    if isinstance(job_requirements, dict):
        reqs_list = job_requirements.get("requirements", [])
        if isinstance(reqs_list, list):
            reqs_text = ", ".join([str(r) if isinstance(r, str) else "" for r in reqs_list[:10]])
    
    location = job_requirements.get("location", "Unknown") if isinstance(job_requirements, dict) else "Unknown"
    
    # Try AI optimization
    ai_result = _optimize_with_ai(cv_text, job_title, reqs_text, location)
    if ai_result and len(ai_result) > 100:
        return ai_result
    
    # Fallback: reorganize CV based on skill matching
    return _optimize_fallback(cv_text, job_title, reqs_text)

def _optimize_with_ai(cv_text, job_title, reqs_text, location):
    """Try AI-powered CV optimization"""
    from api.ai_prompts import OPTIMIZE_CV_SYSTEM_PROMPT, OPTIMIZE_CV_USER_PROMPT_TEMPLATE
    
    user_prompt = OPTIMIZE_CV_USER_PROMPT_TEMPLATE.format(
        job_title=job_title,
        job_description=reqs_text or "General position",
        location=location,
        cv_text=cv_text[:15000]
    )
    
    payload = {
        "model": "nvidia/nemotron-3-nano-4b",
        "messages": [
            {"role": "system", "content": OPTIMIZE_CV_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 6000
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=300)
        result = response.json()
        
        if result.get("choices"):
            content = result["choices"][0].get("message", {}).get("content", "")
            if content and len(content) > 100:
                return content
    except Exception:
        pass
    
    return None

def _optimize_fallback(cv_text, job_title, reqs_text):
    """Generate optimized CV without AI - reorganizes existing content"""
    lines = cv_text.split('\n')
    
    # Extract name (first non-empty line)
    name = "Candidate"
    email = ""
    phone = ""
    for line in lines:
        clean = line.strip()
        if clean and len(clean) < 60:
            name = clean
            break
    
    # Extract contact info
    import re
    for line in lines:
        email_match = re.search(r'\S+@\S+\.\S+', line)
        if email_match:
            email = email_match.group()
        phone_match = re.search(r'[\+]?[\d\s\-\(\)]{9,}', line)
        if phone_match:
            phone = phone_match.group().strip()
    
    # Extract sections
    sections = {"experience": [], "education": [], "skills": [], "other": []}
    current_section = "other"
    section_keywords = {
        "experience": ["experience", "work", "employment", "job", "professional"],
        "education": ["education", "university", "college", "school", "degree", "bachelor", "master"],
        "skills": ["skills", "technologies", "tools", "competencies", "languages"]
    }
    
    for line in lines:
        clean = line.strip().lower()
        for section, keywords in section_keywords.items():
            if any(kw in clean for kw in keywords) and len(clean) < 40:
                current_section = section
                break
        if clean and not any(kw in clean for kw in ["email", "phone", "linkedin"]):
            sections.setdefault(current_section, []).append(line.strip())
    
    # Build optimized CV
    result = []
    result.append(f"# {name}")
    result.append(f"{' | '.join(filter(None, [email, phone]))}")
    result.append("")
    result.append("## PROFESSIONAL PROFILE")
    result.append(f"Professional with experience seeking {job_title} position.")
    if reqs_text:
        result.append(f"Key strengths: {reqs_text}")
    result.append("")
    
    if sections.get("skills"):
        result.append("## SKILLS")
        for s in sections["skills"][:10]:
            if s and len(s) > 1:
                result.append(f"• {s}")
        result.append("")
    
    if sections.get("experience"):
        result.append("## WORK EXPERIENCE")
        for s in sections["experience"][:10]:
            if s and len(s) > 1:
                result.append(f"• {s}")
        result.append("")
    
    if sections.get("education"):
        result.append("## EDUCATION")
        for s in sections["education"][:10]:
            if s and len(s) > 1:
                result.append(f"• {s}")
        result.append("")
    
    if sections.get("other"):
        other = [s for s in sections["other"] if s and len(s) > 1]
        if other:
            result.append("## ADDITIONAL INFORMATION")
            for s in other[:5]:
                result.append(f"• {s}")
            result.append("")
    
    return '\n'.join(result)

def extract_skills_from_text(text):
    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java",
        "C++", "C#", "PHP", "Ruby", "Go", "Rust", "Swift", "Kotlin",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git",
        "HTML", "CSS", "REST", "GraphQL", "Microservices",
        "Machine Learning", "AI", "Data Science", "Big Data",
        "Agile", "Scrum", "DevOps", "Linux", "Security"
    ]
    
    found_skills = []
    text_upper = text.upper()
    for skill in common_skills:
        if skill.upper() in text_upper:
            found_skills.append(skill)
    
    return found_skills[:10] if found_skills else ["Web Development", "Programming"]
