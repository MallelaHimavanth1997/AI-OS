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
    
    # 1. Validate settings
    settings.validate()
    
    # 2. Notify start via Telegram
    notifier = TelegramNotifier()
    await notifier.send_message_async("🤖 <b>AI-OS Master Workflow Started!</b>\nSearching LinkedIn for jobs...")
    
    # 3. Import browser applier
    applier_path = ROOT_DIR / "browser" / "applier.py"
    if applier_path.exists():
        sys.path.insert(0, str(ROOT_DIR / "browser"))
        import applier
        logger.info("Running LinkedIn Applier module...")
        # Run applier in dry run mode or configured mode
        try:
            await applier.main(dry_run=True)
            logger.info("LinkedIn Applier completed successfully.")
        except Exception as e:
            logger.error(f"Error executing LinkedIn Applier: {e}")
            await notifier.send_error(f"LinkedIn Applier error: {e}")
    else:
        logger.warning(f"Applier script not found at {applier_path}")
        
    logger.info("AI-OS Master Workflow finished.")

if __name__ == "__main__":
    asyncio.run(main())
