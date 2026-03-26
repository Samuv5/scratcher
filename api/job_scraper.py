def get_jobs(query="Software Engineer", location="Remote", language="es"):
    # Simulated massive database of jobs. 
    # In a production app, this would be thousands of lines communicating with a PostgreSQL database and dozens of external Scraper services.
    
    base_jobs = [
        {
            "id": "1",
            "title": f"Senior {query}",
            "company": "Tech Innovators Inc.",
            "location": "USA",
            "language": "en",
            "description": f"We are looking for a Senior {query} with 5+ years of experience in Python, FastAPI, and React. Must understand systems architecture and cloud deployments. You will lead teams and manage microservices."
        },
        {
            "id": "2",
            "title": f"Backend {query} Developer",
            "company": "DataCorp LATAM",
            "location": "LATAM",
            "language": "es",
            "description": f"We are looking for backend developers to create APIs using Python and FastAPI. Experience with Postgres and local LLMs is essential."
        },
        {
            "id": "3",
            "title": f"Lead {query}",
            "company": "Startup Hub",
            "location": "Remote",
            "language": "en",
            "description": f"Join our fast-paced startup! As a {query}, you'll work with modern stacks. We need folks familiar with continuous deployment, Git, and Llama3 models for enterprise solutions."
        },
        {
            "id": "4",
            "title": f"Software Engineer ({query})",
            "company": "Fintech Global",
            "location": "LATAM",
            "language": "es",
            "description": "Engineer needed to join the payments team. The position requires strong foundations in security, asynchronous architectures, and automated testing in Python/Java."
        },
        {
            "id": "5",
            "title": f"{query} Architect",
            "company": "EuroTech",
            "location": "Europe",
            "language": "en",
            "description": "Designing high-availability systems for the European market. Required: Docker, Kubernetes, AWS, and strong programming foundations."
        },
        {
            "id": "6",
            "title": f"{query} Remote",
            "company": "Soluciones Ágiles",
            "location": "Remote",
            "language": "es",
            "description": "SaaS company looking to add talent to its ranks working in a 100% remote culture."
        }
    ]

    # Filter by user preference
    filtered_jobs = []
    for job in base_jobs:
        if location.lower() != "remote": # if remote is selected, show all remote jobs everywhere, or specific location
            if job["location"].lower() != location.lower() and job["location"].lower() != "remote":
                continue
        
        if job["language"].lower() != language.lower():
            continue
            
        filtered_jobs.append(job)

    # fallback if filters are too strict
    if not filtered_jobs:
        filtered_jobs = [
            {
                "id": "99",
                "title": f"Global {query} (Fallback)",
                "company": "Crouch Search Placeholder",
                "location": location,
                "language": language,
                "description": "This is a placeholder job because no specific matches were found. We need experience in Python and APIs."
            }
        ]

    return filtered_jobs
