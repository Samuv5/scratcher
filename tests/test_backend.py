"""Tests for Scratcher backend."""

from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app
from api.database import init_db, get_db
from api.cv_optimizer import (
    extract_job_requirements,
    _extract_with_keywords,
    clean_json,
    extract_skills_from_text,
)
from api.job_scraper import get_jobs, _fallback_jobs
from api.templates import render_cv_html, get_template_list, _parse_cv

client = TestClient(app)


class TestHealth:
    def test_health_endpoint(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "Scratcher" in data["app"]


class TestJobs:
    def test_get_jobs_returns_list(self):
        jobs = get_jobs("Developer", "Remote", "en")
        assert isinstance(jobs, list)
        assert len(jobs) > 0

    def test_get_jobs_has_required_fields(self):
        jobs = get_jobs("Python", "Remote", "es")
        for job in jobs[:3]:
            assert "title" in job
            assert "company" in job
            assert "description" in job
            assert "id" in job

    def test_fallback_jobs(self):
        jobs = _fallback_jobs("Test", "Remote", "en")
        assert len(jobs) == 3
        assert jobs[0]["source"] == "Scratcher"

    def test_jobs_api(self):
        response = client.get("/api/jobs?query=Python&location=Remote&language=en")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data


class TestCVOptimizer:
    def test_extract_with_keywords(self):
        text = "We need a Python developer with 5+ years of experience and knowledge of AWS and Docker."
        result = _extract_with_keywords(text)
        assert "title" in result
        assert "requirements" in result
        found = [r.lower() for r in result["requirements"]]
        assert "python" in found
        assert "aws" in found
        assert "docker" in found

    def test_extract_with_keywords_extracts_experience(self):
        text = "We need a Senior Engineer with 5+ years of experience."
        result = _extract_with_keywords(text)
        assert "5+" in result["experience"] or "5" in result["experience"]

    def test_extract_job_requirements_returns_dict(self):
        result = extract_job_requirements("Looking for a React developer with TypeScript skills.")
        assert isinstance(result, dict)
        assert "requirements" in result
        assert "title" in result

    def test_clean_json_removes_comments(self):
        dirty = '{"key": "value", // comment\n"key2": "value2"}'
        clean = clean_json(dirty)
        assert "//" not in clean

    def test_clean_json_removes_trailing_commas(self):
        dirty = '{"key": "value",}'
        clean = clean_json(dirty)
        assert ",}" not in clean

    def test_extract_skills_from_text(self):
        text = "I know Python, JavaScript, and React."
        skills = extract_skills_from_text(text)
        assert len(skills) > 0


class TestTemplates:
    def test_get_template_list(self):
        templates = get_template_list()
        assert len(templates) >= 3
        ids = [t["id"] for t in templates]
        assert "modern" in ids
        assert "classic" in ids
        assert "minimal" in ids

    def test_render_cv_html_modern(self):
        cv = "# John Doe\n\n## Skills\n- Python\n- React\n\n## Experience\n\n### Developer at Corp\n- Built APIs"
        html = render_cv_html(cv, "modern")
        assert "<html" in html
        assert "John Doe" in html
        assert "cv-modern" in html

    def test_render_cv_html_classic(self):
        cv = "# Jane Smith\n\n## Profile\nGood worker."
        html = render_cv_html(cv, "classic")
        assert "Jane Smith" in html
        assert "cv-classic" in html

    def test_render_cv_html_minimal(self):
        cv = "# Bob\n\n## Skills\n- Go"
        html = render_cv_html(cv, "minimal")
        assert "Bob" in html
        assert "cv-minimal" in html
        assert "Go" in html

    def test_parse_cv_parses_sections(self):
        cv = """# John Doe
john@email.com

## Professional Profile
A developer.

## Skills
- Python
- React

## Experience

### Developer at Corp
*2020 - 2023*
- Built APIs
- Wrote tests

## Education

### BS Computer Science
*2016*
- GPA 3.8
"""
        data = _parse_cv(cv)
        assert data["name"] == "John Doe"
        assert data["summary"] == "A developer."
        assert len(data["skills"]) >= 2
        assert len(data["experience"]) >= 1
        assert len(data["education"]) >= 1


class TestAPI:
    def test_upload_cv_no_file(self):
        response = client.post("/api/upload-cv")
        assert response.status_code == 422

    def test_analyze_job_no_url(self):
        response = client.post("/api/analyze-job")
        assert response.status_code == 422

    def test_analyze_job_text_empty(self):
        response = client.post("/api/analyze-job-text", data={"job_text": ""})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_templates_endpoint(self):
        response = client.get("/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data["templates"]) >= 3

    def test_diff_endpoint(self):
        response = client.post(
            "/api/diff",
            data={"original": "Line 1\nLine 2", "optimized": "Line 1\nChanged Line 2"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "changes" in data
        assert data["total_changes"] >= 1

    def test_cvs_list(self):
        response = client.get("/api/cvs")
        assert response.status_code == 200
        assert "cvs" in response.json()

    def test_optimizations_list(self):
        response = client.get("/api/optimizations")
        assert response.status_code == 200
        assert "optimizations" in response.json()
