import os
import re
import sys
import time
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
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

# Import notifications
try:
    from notifications import TelegramNotifier
    def send_telegram_message(msg):
        return TelegramNotifier().send_message_sync(msg)
except ImportError:
    def send_telegram_message(msg):
        print(f"[Telegram]: {msg}")

# Import tailor module
try:
    from tailor import tailor_resume
except ImportError:
    from browser.tailor import tailor_resume

# Configuration
PERSISTENT_CONTEXT_PATH = os.path.abspath("browser_context")

def find_resume_path():
    candidates = [
        os.path.abspath("resumes/resume.txt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../resumes/resume.txt"),
        os.path.abspath("resume.txt")
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

RESUME_PATH = find_resume_path()
TAILORED_PDF_PATH = os.path.abspath("temp_tailored_resume.pdf")

# Default search configurations
JOB_TITLES = ["Data Engineer", "Cloud Data Engineer", "Big Data Engineer", "PySpark Engineer"]
LOCATION = "United States"


# Formats: Workplace Type (Remote = 2, Hybrid = 3)
# URL parameter f_WT=2%2C3 means Remote + Hybrid
JOB_SEARCH_URL_TEMPLATE = "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_WT=2%2C3&f_AL=true"
POSTS_SEARCH_URL_TEMPLATE = "https://www.linkedin.com/search/results/content/?keywords=hiring%20{keywords}%20remote%20email"

# Email Configuration (Outlook default from resume)
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587

async def get_browser_context(playwright, headless=True):
    """Launches Playwright with a persistent profile so cookies/login persist."""
    # Ensure context directory exists
    os.makedirs(PERSISTENT_CONTEXT_PATH, exist_ok=True)
    
    # Launch browser context
    context = await playwright.chromium.launch_persistent_context(
        PERSISTENT_CONTEXT_PATH,
        headless=headless,
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return context

async def check_login_and_authenticate(page):
    """Checks if logged into LinkedIn. If not, prompts user headed to login."""
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    await asyncio.sleep(2) # Settle redirect
    
    # If we are logged in, we should be on the feed page
    if "linkedin.com/feed" in page.url:
        return True
        
    print("🤖 [Robot]: You are not logged in to LinkedIn.")
    send_telegram_message("⚠️ <b>Action Required:</b> LinkedIn robot needs you to log in. A browser window will open on your computer now.")
    return False

async def headed_login_session():
    """Opens a headed browser to let the user login once manually."""
    print("🤖 [Robot]: Opening headed browser for manual LinkedIn login...")
    async with async_playwright() as p:
        context = await get_browser_context(p, headless=False)
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login")
        
        print("\n" + "="*50)
        print("ACTION REQUIRED:")
        print("1. Log in to LinkedIn in the browser window that popped up.")
        print("2. Solve any Captchas or two-factor authentication (2FA).")
        print("3. Once you see your LinkedIn Feed, return here and press ENTER.")
        print("="*50 + "\n")
        
        input("Press Enter here AFTER you have successfully logged in and see your Feed...")
        await context.close()
        print("🤖 [Robot]: Login session saved successfully!")
        send_telegram_message("✅ <b>LinkedIn Login Successful:</b> Robot saved your session cookies.")

def send_resume_via_email(recipient_email, subject, body, pdf_path):
    """Sends the tailored resume PDF via SMTP (Outlook/Gmail)."""
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        print(f"⚠️ [Email Skip]: Credentials not configured. Would have sent email to {recipient_email}")
        return False
        
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach PDF
    try:
        with open(pdf_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {os.path.basename(pdf_path)}',
            )
            msg.attach(part)
    except Exception as e:
        print(f"Failed to attach resume PDF: {e}")
        return False
        
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"📧 [Email Sent]: Tailored application email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")
        return False

async def handle_easy_apply_form(page, dry_run=True):
    """Fills out the Easy Apply modal dialog automatically."""
    print("🤖 [Robot]: Processing Easy Apply Form...")
    
    try:
        # Loop through pages of the multi-step application form
        for step in range(1, 10):
            # Check if there is a next/review button
            next_button = page.locator("button:has-text('Next'), button:has-text('Review')")
            submit_button = page.locator("button:has-text('Submit application')")
            
            # 1. Fill out any text fields, checkboxes, or dropdowns
            # Note: In a production script, we would scan labels and use tailor_resume prompt to answer questions.
            # Here we fill simple text and handle files.
            
            # Handle Resume Upload
            upload_input = page.locator("input[type='file']")
            if await upload_input.count() > 0:
                print("🤖 [Robot]: Uploading tailored resume PDF...")
                await upload_input.first.set_input_files(TAILORED_PDF_PATH)
                await asyncio.sleep(2)
            
            # Use precise aria-label selectors to avoid matching pagination buttons
            next_btn = page.locator("button[aria-label='Continue to next step']")
            review_btn = page.locator("button[aria-label='Review your application']")
            submit_btn = page.locator("button[aria-label='Submit application']")
            
            if await submit_btn.is_visible():
                if dry_run:
                    print("🔍 [Dry Run]: Stopping before clicking 'Submit application'.")
                    await dismiss_easy_apply_modal(page)
                    return True
                else:
                    print("🚀 [Live Run]: Clicking 'Submit application'!")
                    await submit_btn.click()
                    await asyncio.sleep(3)
                    done_button = page.locator("button:has-text('Done')")
                    if await done_button.first.is_visible():
                        await done_button.first.click()
                    return True
            elif await review_btn.is_visible():
                await review_btn.click()
                await asyncio.sleep(1.5)
            elif await next_btn.is_visible():
                await next_btn.click()
                await asyncio.sleep(1.5)
            else:
                break
    except Exception as e:
        print(f"Error filling Easy Apply form: {e}")
        # Always try to dismiss any open modal on error
        await dismiss_easy_apply_modal(page)
        
    return False

async def dismiss_easy_apply_modal(page):
    """Safely closes any open Easy Apply modal dialog."""
    try:
        dismiss_btn = page.locator("button[aria-label='Dismiss']")
        if await dismiss_btn.first.is_visible():
            await dismiss_btn.first.click()
            await asyncio.sleep(1)
        # If LinkedIn asks "Discard application?", click Discard
        discard_btn = page.locator("button[data-control-name='discard_application_confirm_btn'], button:has-text('Discard')")
        if await discard_btn.first.is_visible():
            await discard_btn.first.click()
            await asyncio.sleep(1)
    except Exception:
        pass

async def process_jobs_tab(page, keyword, dry_run=True):
    """Searches for jobs on LinkedIn Jobs Tab and applies."""
    search_url = JOB_SEARCH_URL_TEMPLATE.format(keywords=keyword.replace(" ", "%20"), location=LOCATION.replace(" ", "%20"))
    await page.goto(search_url, wait_until="domcontentloaded")
    await asyncio.sleep(5) # Give it 5 seconds to load fully
    
    # Scroll the job list panel to trigger dynamic loading of cards
    try:
        await page.evaluate("""
            const panel = document.querySelector('.jobs-search-results-list');
            if (panel) {
                panel.scrollTop = panel.scrollHeight;
            }
        """)
        await asyncio.sleep(2)
    except Exception:
        pass

    # Find job cards using multiple possible selector fallbacks
    job_cards = page.locator(".jobs-search-results__list-item, .job-card-container, [data-occludable-job-id]")
    count = await job_cards.count()
    print(f"🤖 [Robot]: Found {count} job listings matching '{keyword}'")
    
    applied_count = 0
    
    for i in range(min(count, 5)): # Limit to top 5 jobs per run for safety/testing
        try:
            # Always dismiss any open modal before clicking the next job card
            await dismiss_easy_apply_modal(page)
            await asyncio.sleep(1)
            
            card = job_cards.nth(i)
            await card.click(force=True)
            await asyncio.sleep(3)
            
            # Extract job title and description using selectors with fallback
            title_el = page.locator(".job-details-jobs-unified-top-card__job-title, h2.t-24, .jobs-unified-top-card__job-title")
            desc_el = page.locator("#job-details, .jobs-description__content, .jobs-box__html-content")
            
            if not await title_el.first.is_visible() or not await desc_el.first.is_visible():
                continue
                
            job_title = await title_el.first.inner_text()
            job_desc = await desc_el.first.inner_text()
            
            print(f"\n📄 [Processing Job]: {job_title.strip()}")
            
            # Generate Tailored Resume
            await tailor_resume(job_desc, job_title, TAILORED_PDF_PATH, RESUME_PATH)
            
            # Click Easy Apply button (with multiple class alternatives)
            apply_button = page.locator("button.jobs-apply-button, button.jobs-apply-button--top-card")
            if await apply_button.first.is_visible():
                await apply_button.first.click()
                await asyncio.sleep(3)
                
                success = await handle_easy_apply_form(page, dry_run)
                if success:
                    applied_count += 1
                    status = "DRY RUN" if dry_run else "SUBMITTED"
                    send_telegram_message(f"💼 <b>Applied ({status}):</b> {job_title.strip()} on LinkedIn Easy Apply.")
            else:
                print("Already applied or not Easy Apply.")
                
        except Exception as e:
            print(f"Failed to process job {i}: {e}")
            # Dismiss modal if it got stuck open
            await dismiss_easy_apply_modal(page)
            
    return applied_count

async def process_posts_feed(page, keyword, dry_run=True):
    """Searches LinkedIn Posts feed for recruiter emails and sends resumes."""
    search_url = POSTS_SEARCH_URL_TEMPLATE.format(keywords=keyword.replace(" ", "%20"))
    await page.goto(search_url, wait_until="domcontentloaded")
    await asyncio.sleep(5)
    
    # Locate post text blocks using robust selectors
    posts = page.locator(".update-components-text, .feed-shared-update-v2__commentary, .feed-shared-update-v2__description, span.break-words")
    count = await posts.count()
    print(f"🤖 [Robot]: Found {count} recruiter posts matching '{keyword}'")
    
    email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails_sent = 0
    
    for i in range(min(count, 5)):
        try:
            post_text = await posts.nth(i).inner_text()
            # Scan post for emails
            emails = re.findall(email_regex, post_text)
            
            if emails:
                target_email = emails[0]
                print(f"\n📧 [Found Recruiter Email]: {target_email} in post {i}")
                
                # Tailor resume for this specific post context
                job_title = f"{keyword} Candidate"
                await tailor_resume(post_text, job_title, TAILORED_PDF_PATH, RESUME_PATH)
                
                # Draft email body using standard cover letter formatting
                subject = f"Data Engineer Application - Himavanth Mallela"
                body = f"""Dear Hiring Team,

I saw your job post on LinkedIn regarding the {keyword} position and would love to apply.

I have 3 years of experience as a Data Engineer specializing in AWS, Azure, PySpark, Snowflake, and DBT. I have attached my tailored resume (PDF) detailing my experience and projects.

Please let me know if we can schedule a time to chat.

Best regards,
Himavanth Mallela
Phone: +1 (314) 393-5056
Email: mallelahimavanth@outlook.com
"""
                if dry_run:
                    print(f"🔍 [Dry Run]: Skip sending email to {target_email}")
                    send_telegram_message(f"📧 <b>Email Prepared (Dry Run):</b> Drafted tailored application email for {target_email}.")
                    emails_sent += 1
                else:
                    success = send_resume_via_email(target_email, subject, body, TAILORED_PDF_PATH)
                    if success:
                        emails_sent += 1
                        send_telegram_message(f"📧 <b>Email Sent:</b> Tailored application email sent to {target_email}.")
                        
        except Exception as e:
            print(f"Failed to process post {i}: {e}")
            
    return emails_sent

async def main(dry_run=True):
    async with async_playwright() as p:
        context = await get_browser_context(p)
        page = await context.new_page()
        
        # 1. Login verification
        logged_in = await check_login_and_authenticate(page)
        
        if not logged_in:
            try:
                await context.close()
            except Exception:
                pass
            # Relaunch headed for manual login
            await headed_login_session()
            # Relaunch context after manual login
            context = await get_browser_context(p)
            page = await context.new_page()
            logged_in = await check_login_and_authenticate(page)
            if not logged_in:
                print("🤖 [Robot]: Relaunch authentication failed.")
                return
        
        easy_applied_total = 0
        emails_sent_total = 0
        
        # Loop through job titles
        for title in JOB_TITLES:
            # Part 1: Jobs Tab
            easy_applied = await process_jobs_tab(page, title, dry_run)
            easy_applied_total += easy_applied
            
            # Part 2: Posts Feed
            emails_sent = await process_posts_feed(page, title, dry_run)
            emails_sent_total += emails_sent
        
        # Final Report
        report = f"""🤖 <b>Job Search Report:</b>
- Easy Apply Submissions: {easy_applied_total}
- Recruiter Emails Sent: {emails_sent_total}
- Mode: {"Dry Run (No Submits)" if dry_run else "Live Applications"}"""
        send_telegram_message(report)
        print(report)
        
        # Clean up temporary PDF
        if os.path.exists(TAILORED_PDF_PATH):
            try:
                os.remove(TAILORED_PDF_PATH)
            except Exception:
                pass
        try:
            await context.close()
        except Exception:
            pass

if __name__ == "__main__":
    # Check arguments: "live" mode runs actual submissions, default is "dry-run"
    is_dry = True
    if len(sys.argv) > 1 and sys.argv[1].lower() == "live":
        is_dry = False
        print("⚠️ RUNNING IN LIVE APPLICATION MODE (Submits applications & sends emails)")
    else:
        print("🔍 RUNNING IN DRY RUN MODE (Safe mode, does not submit or email)")
        
    asyncio.run(main(dry_run=is_dry))
