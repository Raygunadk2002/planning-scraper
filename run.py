#!/usr/bin/env python3
"""
Simple run script for London Planning Application Monitor
Handles basic setup and launches the Streamlit application
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'streamlit',
        'requests', 
        'beautifulsoup4',
        'selenium',
        'pandas',
        'plotly',
        'openpyxl'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Please run: pip install -r requirements.txt")
        return False
    
    return True

def initialize_database():
    """Initialize the database if it doesn't exist"""
    try:
        from database import PlanningDatabase
        db = PlanningDatabase()
        logger.info("✅ Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def check_chrome():
    """Check if Chrome/Chromium is available for Selenium"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
        driver.quit()
        logger.info("✅ Chrome/Selenium is available")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Chrome/Selenium check failed: {e}")
        logger.info("Selenium functionality may be limited, but basic scraping will still work")
        return False

def main():
    """Main function to run the application"""
    logger.info("🏗️ London Planning Application Monitor - Starting...")
    
    # Check current directory
    current_dir = Path.cwd()
    logger.info(f"Running from: {current_dir}")
    
    # Check if we're in the right directory
    if not Path("streamlit_app.py").exists():
        logger.error("❌ streamlit_app.py not found in current directory")
        logger.info("Please run this script from the project root directory")
        sys.exit(1)
    
    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize database
    logger.info("Initializing database...")
    if not initialize_database():
        logger.warning("⚠️ Database initialization had issues, but continuing...")
    
    # Check Chrome (optional)
    logger.info("Checking Chrome/Selenium...")
    check_chrome()
    
    # Launch Streamlit
    logger.info("🚀 Launching Streamlit application...")
    logger.info("The application will open in your default browser")
    logger.info("If it doesn't open automatically, go to: http://localhost:8501")
    
    try:
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 