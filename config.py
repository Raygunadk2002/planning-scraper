"""
Configuration settings for Planning Scraper Application
"""

import os
from typing import List, Dict

# Keywords to search for in planning applications
MONITORING_KEYWORDS = [
    "remote monitoring",
    "noise monitoring", 
    "vibration monitoring",
    "dust monitoring",
    "subsidence monitoring"
]

# London Borough Configuration
BOROUGHS_CONFIG = {
    "Camden": {
        "name": "Camden",
        "base_url": "https://camdenpas.camden.gov.uk",
        "search_url": "https://camdenpas.camden.gov.uk/online-applications/search.do?action=simple&searchType=Application",
        "search_method": "form_based"
    },
    "Westminster": {
        "name": "Westminster", 
        "base_url": "https://idoxpa.westminster.gov.uk",
        "search_url": "https://idoxpa.westminster.gov.uk/online-applications/search.do?action=simple&searchType=Application",
        "search_method": "form_based"  
    },
    "Hammersmith & Fulham": {
        "name": "Hammersmith & Fulham",
        "base_url": "https://public-access.lbhf.gov.uk",
        "search_url": "https://public-access.lbhf.gov.uk/online-applications/search.do?action=simple&searchType=Application",
        "search_method": "form_based"
    },
    "Tower Hamlets": {
        "name": "Tower Hamlets",
        "base_url": "https://development.towerhamlets.gov.uk",
        "search_url": "https://development.towerhamlets.gov.uk/online-applications/search.do?action=simple&searchType=Application", 
        "search_method": "form_based"
    },
    "Southwark": {
        "name": "Southwark",
        "base_url": "https://planning.southwark.gov.uk",
        "search_url": "https://planning.southwark.gov.uk/online-applications/search.do?action=simple&searchType=Application",
        "search_method": "form_based"
    }
}

# Scraping Configuration
SCRAPING_CONFIG = {
    "request_delay": 2.0,  # seconds between requests
    "timeout": 30,  # request timeout in seconds
    "max_retries": 3,
    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "max_pages_per_borough": 10,  # limit scraping to avoid overload
    "respect_robots_txt": True
}

# Database Configuration
DATABASE_CONFIG = {
    "db_path": "planning_applications.db",
    "backup_interval": 100  # backup every N records
}

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "London Planning Application Monitor",
    "page_icon": "🏗️",
    "layout": "wide"
}

# Export Configuration
EXPORT_CONFIG = {
    "csv_filename": "planning_applications_export.csv",
    "excel_filename": "planning_applications_export.xlsx"
} 