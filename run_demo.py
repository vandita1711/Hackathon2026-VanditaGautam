import asyncio
import os
import subprocess
import sys
from app.core.logger import logger

def run_demo():
    """
    Wrapper script to ensure data is generated before running main.py --demo
    """
    logger.info("Starting ShopWave Hackathon Demo Workflow...")
    
    # 1. Generate Data
    if os.path.exists("scripts/generate_data.py"):
        logger.info("Generating mock data...")
        subprocess.run([sys.executable, "scripts/generate_data.py"], check=True)
    else:
        logger.error("scripts/generate_data.py not found. Please ensure it exists.")
        return

    # 2. Run Main Demo
    logger.info("Executing Autonomous Agent Pipeline...")
    subprocess.run([sys.executable, "main.py", "--demo"], check=True)

if __name__ == "__main__":
    run_demo()
