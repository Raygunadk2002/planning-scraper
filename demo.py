#!/usr/bin/env python3
"""
Demonstration script for London Planning Application Monitor
Creates sample data and shows basic functionality
"""

import logging
from datetime import datetime, timedelta
import random

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_data():
    """Create sample planning applications for demonstration"""
    from database import PlanningDatabase
    from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS
    
    # Initialize database
    db = PlanningDatabase()
    
    # Sample application data
    sample_applications = [
        {
            'project_id': '2024/001234/PA',
            'borough': 'Camden',
            'title': 'Construction of 50-unit residential development with noise monitoring system',
            'address': '123 Camden High Street, London NW1 7JN',
            'submission_date': '2024-01-15',
            'application_url': 'https://camdenpas.camden.gov.uk/online-applications/application-details/2024/001234/PA',
            'detected_keywords': ['noise monitoring'],
            'source_url': 'https://camdenpas.camden.gov.uk/online-applications/search'
        },
        {
            'project_id': 'APP/2024/567',
            'borough': 'Westminster',
            'title': 'Office redevelopment with dust and vibration monitoring during construction',
            'address': '456 Oxford Street, London W1C 1AP',
            'submission_date': '2024-01-20',
            'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/application-details/APP/2024/567',
            'detected_keywords': ['dust monitoring', 'vibration monitoring'],
            'source_url': 'https://idoxpa.westminster.gov.uk/online-applications/search'
        },
        {
            'project_id': '24/00789/FUL',
            'borough': 'Hammersmith & Fulham',
            'title': 'Hotel development with comprehensive environmental monitoring suite',
            'address': '789 King Street, London W6 9NH',
            'submission_date': '2024-02-01',
            'application_url': 'https://public-access.lbhf.gov.uk/online-applications/application-details/24/00789/FUL',
            'detected_keywords': ['remote monitoring', 'noise monitoring', 'dust monitoring'],
            'source_url': 'https://public-access.lbhf.gov.uk/online-applications/search'
        },
        {
            'project_id': 'PA/TH/2024/101',
            'borough': 'Tower Hamlets',
            'title': 'Residential tower with subsidence monitoring for adjacent historic buildings',
            'address': '101 Commercial Street, London E1 6BF',
            'submission_date': '2024-02-10',
            'application_url': 'https://development.towerhamlets.gov.uk/online-applications/application-details/PA/TH/2024/101',
            'detected_keywords': ['subsidence monitoring'],
            'source_url': 'https://development.towerhamlets.gov.uk/online-applications/search'
        },
        {
            'project_id': '24/AP/0234',
            'borough': 'Southwark',
            'title': 'Mixed-use development with noise and vibration monitoring plan',
            'address': '234 Borough High Street, London SE1 1JX',
            'submission_date': '2024-02-15',
            'application_url': 'https://planning.southwark.gov.uk/online-applications/application-details/24/AP/0234',
            'detected_keywords': ['noise monitoring', 'vibration monitoring'],
            'source_url': 'https://planning.southwark.gov.uk/online-applications/search'
        },
        {
            'project_id': '2024/002468/PA',
            'borough': 'Camden',
            'title': 'Infrastructure project requiring remote environmental monitoring',
            'address': '246 Euston Road, London NW1 2DB',
            'submission_date': '2024-02-20',
            'application_url': 'https://camdenpas.camden.gov.uk/online-applications/application-details/2024/002468/PA',
            'detected_keywords': ['remote monitoring'],
            'source_url': 'https://camdenpas.camden.gov.uk/online-applications/search'
        },
        {
            'project_id': 'APP/2024/890',
            'borough': 'Westminster',
            'title': 'Underground parking with subsidence monitoring requirements',
            'address': '890 Piccadilly, London W1J 9HP',
            'submission_date': '2024-03-01',
            'application_url': 'https://idoxpa.westminster.gov.uk/online-applications/application-details/APP/2024/890',
            'detected_keywords': ['subsidence monitoring'],
            'source_url': 'https://idoxpa.westminster.gov.uk/online-applications/search'
        }
    ]
    
    # Insert sample data
    total, new = db.bulk_insert_applications(sample_applications)
    logger.info(f"Sample data created: {new} new applications out of {total} total")
    
    return len(sample_applications)

def demonstrate_database_operations():
    """Demonstrate database operations"""
    logger.info("Demonstrating database operations...")
    
    from database import PlanningDatabase
    
    db = PlanningDatabase()
    
    # Get statistics
    stats = db.get_statistics()
    logger.info(f"Database statistics:")
    logger.info(f"  Total applications: {stats.get('total_applications', 0)}")
    logger.info(f"  Boroughs with data: {len(stats.get('by_borough', {}))}")
    
    # Show breakdown by borough
    logger.info("Applications by borough:")
    for borough, count in stats.get('by_borough', {}).items():
        logger.info(f"  {borough}: {count}")
    
    # Show breakdown by keyword
    logger.info("Applications by monitoring type:")
    for keyword, count in stats.get('by_keyword', {}).items():
        if count > 0:
            logger.info(f"  {keyword}: {count}")
    
    # Demonstrate filtering
    logger.info("\nDemonstrating data filtering...")
    
    # Get Westminster applications
    westminster_apps = db.get_applications(borough="Westminster")
    logger.info(f"Westminster applications: {len(westminster_apps)}")
    
    # Get noise monitoring applications
    noise_apps = db.get_applications(keyword="noise monitoring")
    logger.info(f"Noise monitoring applications: {len(noise_apps)}")
    
    return True

def demonstrate_text_processing():
    """Demonstrate text processing capabilities"""
    logger.info("Demonstrating text processing...")
    
    from utils import TextProcessor
    
    # Sample text from a planning application
    sample_text = """
    PLANNING APPLICATION DESCRIPTION:
    
    Construction of a 15-storey residential building comprising 120 residential units.
    
    ENVIRONMENTAL MONITORING:
    The development will include comprehensive noise monitoring throughout the construction phase.
    Real-time dust monitoring systems will be installed at all site boundaries.
    Vibration monitoring will be conducted for nearby sensitive buildings.
    A subsidence monitoring program will monitor ground movement effects.
    Remote monitoring capabilities will provide 24/7 oversight of all environmental parameters.
    
    All monitoring data will be available to the local authority via secure web portal.
    """
    
    # Clean text
    cleaned = TextProcessor.clean_text(sample_text)
    logger.info(f"Text length: {len(cleaned)} characters")
    
    # Detect keywords
    keywords = TextProcessor.detect_keywords(cleaned)
    logger.info(f"Detected monitoring keywords: {keywords}")
    
    # Test project ID extraction
    test_ids = [
        "Reference: 2024/001234/PA",
        "Application APP/2024/567 submitted",
        "Planning ref: 24/00789/FUL"
    ]
    
    for test_text in test_ids:
        project_id = TextProcessor.extract_project_id(test_text)
        logger.info(f"'{test_text}' → Project ID: {project_id}")
    
    return True

def demonstrate_scraper_creation():
    """Demonstrate scraper creation"""
    logger.info("Demonstrating scraper creation...")
    
    from scrapers import create_scraper
    from config import BOROUGHS_CONFIG
    
    for borough_name in BOROUGHS_CONFIG.keys():
        try:
            scraper = create_scraper(borough_name)
            logger.info(f"✅ Created scraper for {borough_name} ({type(scraper).__name__})")
            
            # Clean up Selenium scrapers
            if hasattr(scraper, 'close'):
                scraper.close()
                
        except Exception as e:
            logger.error(f"❌ Failed to create scraper for {borough_name}: {e}")
    
    return True

def demonstrate_manager():
    """Demonstrate scraper manager"""
    logger.info("Demonstrating scraper manager...")
    
    from scraper_manager import ScrapingManager
    
    # Initialize manager
    manager = ScrapingManager()
    
    # Get status
    status = manager.get_scraping_status()
    logger.info(f"Manager initialized with {status['total_boroughs']} borough scrapers")
    
    # Show current status
    logger.info("Current scraping status:")
    for borough, info in status.get('boroughs', {}).items():
        logger.info(f"  {borough}: {info['status']}")
    
    # Clean up
    manager.cleanup()
    
    return True

def run_full_demo():
    """Run complete demonstration"""
    logger.info("🎭 Starting London Planning Application Monitor Demonstration")
    
    demos = [
        ("Creating Sample Data", create_sample_data),
        ("Database Operations", demonstrate_database_operations),
        ("Text Processing", demonstrate_text_processing),
        ("Scraper Creation", demonstrate_scraper_creation),
        ("Manager Operations", demonstrate_manager)
    ]
    
    success_count = 0
    
    for demo_name, demo_func in demos:
        logger.info(f"\n--- {demo_name} ---")
        try:
            result = demo_func()
            if result:
                success_count += 1
                logger.info(f"✅ {demo_name} completed successfully")
            else:
                logger.warning(f"⚠️ {demo_name} completed with warnings")
        except Exception as e:
            logger.error(f"❌ {demo_name} failed: {e}")
    
    # Summary
    logger.info(f"\n🎯 Demo Summary: {success_count}/{len(demos)} successful")
    
    if success_count == len(demos):
        logger.info("🎉 All demonstrations completed successfully!")
        logger.info("You can now start the application with: streamlit run streamlit_app.py")
    else:
        logger.warning("⚠️ Some demonstrations had issues. Check the logs above.")
    
    return success_count == len(demos)

def main():
    """Main demo function"""
    try:
        success = run_full_demo()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\n👋 Demo interrupted by user")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 