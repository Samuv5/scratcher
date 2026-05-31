import requests
import re
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import quote
from loguru import logger

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}

TIMEOUT = 15


def scrape_indeed(query, location="remote", limit=10):
    """Scrape job listings from Indeed."""
    jobs = []
    try:
        loc_param = quote(location)
        q_param = quote(query)
        url = f"https://es.indeed.com/jobs?q={q_param}&l={loc_param}&limit={limit}"
        
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("[class*='job_seen_beacon'], [class*='cardOutline'], .job-card")
        
        for card in cards[:limit]:
            try:
                title_el = card.select_one("h2 a, [class*='jobTitle'] a, h2[class*='title']")
                company_el = card.select_one("[class*='companyName'], [class*='company']")
                location_el = card.select_one("[class*='companyLocation'], [class*='location']")
                desc_el = card.select_one("[class*='job-snippet'], [class*='summary']")
                
                title = title_el.get_text(strip=True) if title_el else query
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc = location_el.get_text(strip=True) if location_el else location
                desc = desc_el.get_text(strip=True) if desc_el else f"We are looking for a {title}."
                
                link_el = title_el.get("href") if title_el and hasattr(title_el, "get") else ""
                link = f"https://es.indeed.com{link_el}" if link_el and link_el.startswith("/") else ""
                
                jobs.append({
                    "id": f"indeed-{len(jobs)}",
                    "title": title,
                    "company": company,
                    "location": loc,
                    "language": "es",
                    "description": desc[:800],
                    "source": "Indeed",
                    "url": link,
                })
            except Exception as e:
                logger.debug(f"Error parsing Indeed card: {e}")
                continue
        
        logger.info(f"Indeed: found {len(jobs)} jobs for '{query}'")
    except Exception as e:
        logger.warning(f"Indeed scraper failed: {e}")
    
    return jobs


def scrape_linkedin(query, location="remote", limit=10):
    """Scrape job listings from LinkedIn."""
    jobs = []
    try:
        q_param = quote(query)
        loc_param = quote(location if location != "remote" else "Remote")
        url = f"https://www.linkedin.com/jobs/search/?keywords={q_param}&location={loc_param}&start=0"
        
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".job-search-card, [class*='job-card'], .base-card")
        
        for card in cards[:limit]:
            try:
                title_el = card.select_one("h3 a, [class*='job-title'] a, h3[class*='title']")
                company_el = card.select_one("[class*='company-name'], [class*='company'] a, h4 a")
                location_el = card.select_one("[class*='job-location'], [class*='location']")
                
                title = title_el.get_text(strip=True) if title_el else query
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc = location_el.get_text(strip=True) if location_el else location
                
                link = ""
                if title_el and title_el.name == "a":
                    link = title_el.get("href", "")
                elif title_el:
                    parent_a = title_el.find_parent("a")
                    if parent_a:
                        link = parent_a.get("href", "")
                
                lang = "en"
                desc_keywords = ["buscamos", "requisitos", "experiencia", "empresa"]
                if any(kw in (title + " " + company + " " + loc).lower() for kw in desc_keywords):
                    lang = "es"
                
                jobs.append({
                    "id": f"linkedin-{len(jobs)}",
                    "title": title,
                    "company": company,
                    "location": loc,
                    "language": lang,
                    "description": f"Position: {title} at {company}. Location: {loc}.",
                    "source": "LinkedIn",
                    "url": link,
                })
            except Exception as e:
                logger.debug(f"Error parsing LinkedIn card: {e}")
                continue
        
        logger.info(f"LinkedIn: found {len(jobs)} jobs for '{query}'")
    except Exception as e:
        logger.warning(f"LinkedIn scraper failed: {e}")
    
    return jobs


def scrape_computrabajo(query, location="", limit=10):
    """Scrape job listings from Computrabajo."""
    jobs = []
    try:
        q_param = quote(query)
        url = f"https://www.computrabajo.com.mx/ofertas-de-trabajo/?q={q_param}"
        if location:
            url += f"&l={quote(location)}"
        
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select("[class*='box'], [class*='offer'], article, .job-item")
        
        for card in cards[:limit]:
            try:
                title_el = card.select_one("h2 a, h2[class*='title'] a, [class*='jobTitle'] a, h2")
                company_el = card.select_one("[class*='company'], [class*='empresa'], .author")
                location_el = card.select_one("[class*='location'], [class*='ubicacion'], .city")
                desc_el = card.select_one("[class*='description'], [class*='descripcion'], p")
                
                title = title_el.get_text(strip=True) if title_el else query
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc = location_el.get_text(strip=True) if location_el else (location or "México")
                desc = desc_el.get_text(strip=True) if desc_el else f"Job offer for {title} at {company}."
                
                link = ""
                if title_el and title_el.name == "a":
                    link = title_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = f"https://www.computrabajo.com.mx{link}"
                
                jobs.append({
                    "id": f"computrabajo-{len(jobs)}",
                    "title": title,
                    "company": company,
                    "location": loc,
                    "language": "es",
                    "description": desc[:800],
                    "source": "Computrabajo",
                    "url": link,
                })
            except Exception as e:
                logger.debug(f"Error parsing Computrabajo card: {e}")
                continue
        
        logger.info(f"Computrabajo: found {len(jobs)} jobs for '{query}'")
    except Exception as e:
        logger.warning(f"Computrabajo scraper failed: {e}")
    
    return jobs


def get_jobs(query="Software Developer", location="Remote", language="es"):
    """Scrape jobs from multiple sources. Returns merged list."""
    all_jobs = []
    
    # Parallel scraping with delays to avoid rate limiting
    scrapers = [
        ("Indeed", lambda: scrape_indeed(query, location)),
        ("LinkedIn", lambda: scrape_linkedin(query, location)),
    ]
    
    if language.lower() == "es":
        scrapers.append(("Computrabajo", lambda: scrape_computrabajo(query, location)))
    
    for name, scraper_fn in scrapers:
        try:
            jobs = scraper_fn()
            all_jobs.extend(jobs)
            time.sleep(1)  # Be polite between requests
        except Exception as e:
            logger.warning(f"Scraper {name} failed: {e}")
    
    # Filter by language preference
    if language == "es":
        all_jobs = [j for j in all_jobs if j.get("language", "en") == "es"] or all_jobs
    elif language == "en":
        all_jobs = [j for j in all_jobs if j.get("language", "en") == "en"] or all_jobs
    
    # Limit total results
    all_jobs = all_jobs[:20]
    
    # Fallback if all scrapers fail
    if not all_jobs:
        logger.info("All scrapers failed, using fallback jobs")
        all_jobs = _fallback_jobs(query, location, language)
    
    # Shuffle for variety
    import random
    random.shuffle(all_jobs)
    
    # Add sequential IDs
    for i, job in enumerate(all_jobs):
        job["id"] = str(i + 1)
    
    return all_jobs


def _fallback_jobs(query, location, language):
    """Fallback when all scrapers fail."""
    lang = "es" if language == "es" else "en"
    fallbacks = [
        {
            "title": f"Senior {query}",
            "company": "Tech Corp",
            "location": "Remote",
            "language": lang,
            "description": f"We are looking for a Senior {query} with experience in modern technologies. Join our team!",
            "source": "Scratcher",
        },
        {
            "title": f"{query} - Full Stack",
            "company": "StartupXYZ",
            "location": location,
            "language": lang,
            "description": f"Full stack {query} needed. Work with cutting-edge tech and a great team.",
            "source": "Scratcher",
        },
        {
            "title": f"Junior {query}",
            "company": "Innovation Lab",
            "location": "Remote",
            "language": lang,
            "description": f"Great opportunity for a junior {query}. Grow your career with us!",
            "source": "Scratcher",
        },
    ]
    for i, job in enumerate(fallbacks):
        job["id"] = str(i + 1)
    return fallbacks
