import os
import json
import asyncio
from google import genai
from google.genai import types
from jinja2 import Template
from playwright.async_api import async_playwright

def load_env():
    """Loads environment variables from .env file."""
    paths = [
        ".env",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../.env"),
        os.path.abspath("C:/Users/Himavanth Mallela/.gemini/antigravity/scratch/job-search-agent/.env")
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()
            break

# Load keys
load_env()

# Initialize the Gemini Client
try:
    client = genai.Client()
except Exception:
    client = None

RESUME_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ name }} - Resume</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            color: #2D3748;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            font-size: 11pt;
            background-color: #FFFFFF;
        }
        .container {
            padding: 0;
            max-width: 800px;
            margin: 0 auto;
        }
        header {
            border-bottom: 2px solid #3182CE;
            padding-bottom: 12px;
            margin-bottom: 16px;
        }
        h1 {
            font-size: 24pt;
            font-weight: 700;
            color: #1A365D;
            margin: 0 0 4px 0;
            letter-spacing: -0.5px;
        }
        .title {
            font-size: 14pt;
            font-weight: 500;
            color: #3182CE;
            margin: 0 0 8px 0;
        }
        .contact-info {
            font-size: 9.5pt;
            color: #718096;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }
        .contact-info span {
            display: inline-block;
        }
        h2 {
            font-size: 12pt;
            font-weight: 600;
            color: #1A365D;
            border-bottom: 1px solid #E2E8F0;
            padding-bottom: 4px;
            margin: 18px 0 8px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        p.summary {
            margin: 0 0 12px 0;
            text-align: justify;
            font-size: 10pt;
        }
        .skills-grid {
            display: grid;
            grid-template-columns: 180px 1fr;
            row-gap: 4px;
            column-gap: 12px;
            font-size: 9.5pt;
            margin-bottom: 12px;
        }
        .skills-category {
            font-weight: 600;
            color: #4A5568;
        }
        .skills-list {
            color: #2D3748;
        }
        .job, .project {
            margin-bottom: 14px;
        }
        .job-header, .project-header {
            display: flex;
            justify-content: space-between;
            font-weight: 600;
            font-size: 10.5pt;
            color: #2D3748;
            margin-bottom: 4px;
        }
        .company-role {
            color: #1A365D;
        }
        .job-dates, .project-dates {
            color: #718096;
            font-size: 9.5pt;
            font-weight: 400;
        }
        ul {
            margin: 0;
            padding-left: 20px;
            font-size: 9.5pt;
        }
        li {
            margin-bottom: 4px;
            text-align: justify;
        }
        .education-item {
            display: flex;
            justify-content: space-between;
            font-size: 10pt;
        }
        .edu-degree {
            font-weight: 600;
            color: #2D3748;
        }
        .edu-school {
            color: #4A5568;
        }
        .edu-dates {
            color: #718096;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ name }}</h1>
            <div class="title">{{ target_title }}</div>
            <div class="contact-info">
                <span><strong>Phone:</strong> {{ phone }}</span>
                <span><strong>Email:</strong> {{ email }}</span>
                {% if website %}<span><strong>LinkedIn:</strong> {{ website }}</span>{% endif %}
            </div>
        </header>

        <section>
            <h2>Professional Summary</h2>
            <p class="summary">{{ summary }}</p>
        </section>

        <section>
            <h2>Technical Skills</h2>
            <div class="skills-grid">
                {% for category, items in skills.items() %}
                <div class="skills-category">{{ category }}</div>
                <div class="skills-list">{{ items }}</div>
                {% endfor %}
            </div>
        </section>

        <section>
            <h2>Professional Experience</h2>
            {% for job in experience %}
            <div class="job">
                <div class="job-header">
                    <span class="company-role"><strong>{{ job.role }}</strong> – {{ job.client }}</span>
                    <span class="job-dates">{{ job.dates }}</span>
                </div>
                <ul>
                    {% for bullet in job.bullets %}
                    <li>{{ bullet }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </section>

        <section>
            <h2>Projects</h2>
            {% for proj in projects %}
            <div class="project">
                <div class="project-header">
                    <span class="company-role"><strong>{{ proj.title }}</strong></span>
                </div>
                <ul>
                    {% for bullet in proj.bullets %}
                    <li>{{ bullet }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </section>

        <section>
            <h2>Education</h2>
            <div class="education-item">
                <span class="edu-degree"><strong>{{ education.degree }}</strong> <span class="edu-school">| {{ education.school }}</span></span>
                <span class="edu-dates">{{ education.dates }}</span>
            </div>
        </section>
        
        {% if certifications %}
        <section>
            <h2>Certifications</h2>
            <ul>
                {% for cert in certifications %}
                <li>{{ cert }}</li>
                {% endfor %}
            </ul>
        </section>
        {% endif %}
    </div>
</body>
</html>
"""

def load_resume_text(resume_path="resume.txt"):
    """Loads the base resume content."""
    if not os.path.exists(resume_path):
        # Fallback default values if file doesn't exist
        return ""
    with open(resume_path, "r", encoding="utf-8") as f:
        return f.read()

async def generate_tailored_resume_json(resume_text: str, job_description: str, job_title: str):
    """Uses Gemini API to rewrite the resume text tailored to the job description."""
    if not client:
        raise ValueError("Gemini Client not initialized. Please check GEMINI_API_KEY environment variable.")
        
    prompt = f"""
You are an expert resume writer and career coach. Your task is to rewrite a candidate's resume so that it is tailored to a specific job description. 
Do not lie or make up achievements. Instead, rephrase, highlight, and prioritize experience, skills, and projects that directly match the keywords and requirements in the job description.

Original Resume:
{resume_text}

Target Job Title:
{job_title}

Job Description:
{job_description}

Provide the tailored resume strictly in JSON format. The response should match this exact JSON schema:
{{
  "name": "Himavanth Mallela",
  "phone": "+1 (314) 393-5056",
  "email": "mallelahimavanth@outlook.com",
  "target_title": "Data Engineer",
  "summary": "A 3-4 sentence professional summary tailored to the job description.",
  "skills": {{
    "Cloud Platforms": "Comma separated list of matching cloud platforms",
    "Big Data & Streaming": "Comma separated list of streaming/big data tools",
    "Databases": "Comma separated list of databases",
    "Programming Languages": "Comma separated list of programming languages",
    "Tools & IDEs": "Comma separated list of tools",
    "Visualization & BI": "Comma separated list of BI tools",
    "DevOps & CI/CD": "Comma separated list of devops tools"
  }},
  "experience": [
    {{
      "client": "UPL (United Phosphorus Limited), India",
      "role": "Data Engineer",
      "dates": "May 2021 – July 2023",
      "bullets": [
        "Tailored bullet point 1 focusing on job description keywords",
        "Tailored bullet point 2 focusing on job description keywords",
        "Tailored bullet point 3 focusing on job description keywords"
      ]
    }}
  ],
  "projects": [
    {{
      "title": "ETL Pipeline for Sales and Inventory Data",
      "bullets": [
        "Tailored bullet point 1",
        "Tailored bullet point 2"
      ]
    }},
    {{
      "title": "Real-Time Data Capture Pipeline (Kafka -> Lambda -> S3)",
      "bullets": [
        "Tailored bullet point 1"
      ]
    }},
    {{
      "title": "Data Lake Migration Project",
      "bullets": [
        "Tailored bullet point 1",
        "Tailored bullet point 2"
      ]
    }}
  ],
  "education": {{
    "degree": "Master’s in Information Technology (3.9/4.0 GPA)",
    "school": "Webster University, Saint Louis, Missouri, USA",
    "dates": "Completed"
  }},
  "certifications": [
    "AWS Certified Developer – Associate",
    "Azure Developer Associate"
  ]
}}

Ensure all fields are fully populated and relevant. Keep the bullet points clear, metric-driven, and highly relevant. Return ONLY valid JSON, do not include markdown blocks.
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text.strip())

async def render_html_to_pdf(html_content: str, output_pdf_path: str):
    """Uses Playwright to print the HTML template into a PDF file."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Set content directly
        await page.set_content(html_content)
        
        # Wait for fonts to load
        await page.evaluate("document.fonts.ready")
        
        # Save to PDF
        await page.pdf(
            path=output_pdf_path,
            format="A4",
            margin={
                "top": "0.4in",
                "right": "0.4in",
                "bottom": "0.4in",
                "left": "0.4in"
            },
            print_background=True
        )
        await browser.close()

async def tailor_resume(job_description: str, job_title: str, output_pdf_path="tailored_resume.pdf", resume_path="resume.txt"):
    """Main function to tailor the resume and output it as a PDF."""
    print(f"Tailoring resume for: {job_title}")
    resume_text = load_resume_text(resume_path)
    
    # 1. Generate tailored data structure using Gemini
    tailored_data = await generate_tailored_resume_json(resume_text, job_description, job_title)
    
    # 2. Render to HTML using Jinja2
    template = Template(RESUME_HTML_TEMPLATE)
    html_content = template.render(**tailored_data)
    
    # 3. Print HTML to PDF
    await render_html_to_pdf(html_content, output_pdf_path)
    print(f"Successfully generated tailored PDF: {output_pdf_path}")
    return output_pdf_path

if __name__ == "__main__":
    # Test block
    test_jd = """
    We are looking for a Senior Data Engineer with extensive experience in Apache Spark, PySpark, Databricks, and cloud data platforms like AWS and GCP. 
    You will build ETL pipelines, design database structures using Snowflake, and work on data lake migrations. Experience with Kafka for streaming is a plus.
    """
    # Simple test run (requires GEMINI_API_KEY)
    if os.getenv("GEMINI_API_KEY"):
        asyncio.run(tailor_resume(test_jd, "Senior Data Engineer", "test_resume.pdf", "../../resume.txt"))
    else:
        print("GEMINI_API_KEY not found. Skipping test execution.")
