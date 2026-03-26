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
        
        # Eliminar scripts y estilos
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator=' ', strip=True)
        
        # Limpiar texto
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
            
            # Extraer JSON de bloques de código si existen
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            # Limpiar el JSON
            content = clean_json(content)
            
            try:
                parsed = json.loads(content)
                # Ensure it has the necessary keys
                return {
                    "title": parsed.get("title", "Position"),
                    "requirements": parsed.get("requirements", []),
                    "experience": parsed.get("experience", "Not specified"),
                    "languages": parsed.get("languages", []),
                    "responsibilities": parsed.get("responsibilities", [])
                }
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"Content: {content[:500]}")
    except Exception as e:
        print(f"Error calling AI: {e}")
    
    return {
        "title": "Position",
        "requirements": [],
        "experience": "Not specified",
        "languages": [],
        "responsibilities": []
    }

def optimize_cv_with_job(cv_text, job_requirements, job_title):
    """Optimize CV based on user's REAL skills and job requirements"""
    
    # Prepare short requirements text
    if isinstance(job_requirements, dict):
        reqs_list = job_requirements.get("requirements", [])
        if isinstance(reqs_list, list):
            reqs_text = ", ".join([str(r) if isinstance(r, str) else str(r.get("general_skills", [""])[0]) if isinstance(r, dict) else "" for r in reqs_list[:10]])
        else:
            reqs_text = str(reqs_list)[:500]
    else:
        reqs_text = str(job_requirements)[:500]
    
    prompt = f"""You are an HR expert. Optimize this CV for the requested position.

IMPORTANT RULES:
1. PRESERVE all dates, companies, and original positions
2. DO NOT invent experience or dates
3. PRIORITIZE skills that match the position
4. KEEP original contact information
5. Include ALL relevant content from the original CV

ORIGINAL CV:
{cv_text[:15000]}

TARGET POSITION: {job_title}
KEY REQUIREMENTS: {reqs_text}

Generate a complete CV with this EXACT format:

# [FULL NAME]
[Email] | [Phone] | [Location] | [LinkedIn if available]

## PROFESSIONAL PROFILE
[2-3 lines summarizing experience and objective]

## TECHNICAL SKILLS
• [Skill 1]
• [Skill 2]
[etc]

## WORK EXPERIENCE

### [Position] - [Company]
*[Month Year] - [Month Year] | [City]*
• [Achievement/responsibility 1]
• [Achievement/responsibility 2]
[Repeat for each job]

## EDUCATION

### [Degree] - [Institution]
*[Graduation year]*
[Relevant details]

## OTHERS
• Languages: [if applicable]
• Certifications: [if applicable]

Generate MINIMUM 600 words. Use ALL relevant content from the original CV."""

    payload = {
        "model": "nvidia/nemotron-3-nano-4b",
        "messages": [
            {
                "role": "system",
                "content": "You adapt CVs. Only use real information. Respond in plain text with simple markdown formatting."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.5,
        "max_tokens": 6000
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=300)
        result = response.json()
        
        if result.get("choices"):
            content = result["choices"][0].get("message", {}).get("content", "")
            if content and len(content) > 50:
                return content
    except Exception as e:
        print(f"Error calling AI for optimize: {e}")
    
    # Fallback: generate basic CV with available info
    return f"""# {job_title}

## Professional Profile
Professional with relevant experience for the {job_title} position.

## Relevant Skills
{reqs_text[:300] if reqs_text else 'Skills detected in your CV'}

## Experience
Experience documented in your original CV.

## Note
This is a basic CV. For complete optimization, try again or adjust manually according to job requirements."""

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
