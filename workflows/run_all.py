"""Master Workflow Runner for AI-OS.

Executes job search, resume tailoring, LinkedIn Easy Apply, email outreach, and notification updates.
"""

import sys
import os
import asyncio
from pathlib import Path

# Ensure AI-OS root is in Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import settings
from notifications import notify, TelegramNotifier
from utils import get_logger

logger = get_logger("workflows.run_all")

async def main():
    logger.info("Starting AI-OS Master Workflow...")
    
    # Check dry_run flag from command line or env
    is_live = "--live" in sys.argv or os.getenv("DRY_RUN", "true").lower() == "false"
    dry_run = not is_live
    mode_str = "🚀 LIVE MODE (Submitting real applications)" if is_live else "🔍 DRY RUN MODE (Safe mode, no submits)"
    logger.info(f"Execution Mode: {mode_str}")
    
    # 2. Notify start via Telegram
    notifier = TelegramNotifier()
    await notifier.send_message_async(f"🤖 <b>AI-OS Master Workflow Started!</b>\nMode: {mode_str}\nSearching LinkedIn for jobs...")
    
    # 3. Import browser applier
    applier_path = ROOT_DIR / "browser" / "applier.py"
    if applier_path.exists():
        sys.path.insert(0, str(ROOT_DIR / "browser"))
        import applier
        logger.info("Running LinkedIn Applier module...")
        try:
            await applier.main(dry_run=dry_run)
            logger.info("LinkedIn Applier completed successfully.")
        except Exception as e:
            logger.error(f"Error executing LinkedIn Applier: {e}")
            await notifier.send_error(f"LinkedIn Applier error: {e}")
    else:
        logger.warning(f"Applier script not found at {applier_path}")
        
    logger.info("AI-OS Master Workflow finished.")

if __name__ == "__main__":
    asyncio.run(main())
