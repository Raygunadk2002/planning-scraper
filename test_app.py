#!/usr/bin/env python3
"""
Test script for London Planning Application Monitor
Verifies basic functionality of all components
"""

import sys
import logging
from typing import Dict, List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import config
        logger.info("✅ config module imported")
        
        import database
        logger.info("✅ database module imported")
        
        import utils
        logger.info("✅ utils module imported")
        
        import scrapers
        logger.info("✅ scrapers module imported")
        
        import scraper_manager
        logger.info("✅ scraper_manager module imported")
        
        # Test external dependencies
        import streamlit
        import requests
        import pandas as pd
        import plotly.express as px
        from bs4 import BeautifulSoup
        logger.info("✅ All external dependencies imported")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration module"""
    logger.info("Testing configuration...")
    
    try:
        from config import BOROUGHS_CONFIG, MONITORING_KEYWORDS, SCRAPING_CONFIG
        
        # Check boroughs
        assert len(BOROUGHS_CONFIG) == 5, f"Expected 5 boroughs, got {len(BOROUGHS_CONFIG)}"
        required_boroughs = ["Camden", "Westminster", "Hammersmith & Fulham", "Tower Hamlets", "Southwark"]
        
        for borough in required_boroughs:
            assert borough in BOROUGHS_CONFIG, f"Missing borough: {borough}"
            assert 'base_url' in BOROUGHS_CONFIG[borough], f"Missing base_url for {borough}"
            assert 'search_url' in BOROUGHS_CONFIG[borough], f"Missing search_url for {borough}"
        
        # Check keywords
        assert len(MONITORING_KEYWORDS) == 5, f"Expected 5 keywords, got {len(MONITORING_KEYWORDS)}"
        expected_keywords = ["remote monitoring", "noise monitoring", "vibration monitoring", "dust monitoring", "subsidence monitoring"]
        
        for keyword in expected_keywords:
            assert keyword in MONITORING_KEYWORDS, f"Missing keyword: {keyword}"
        
        logger.info("✅ Configuration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    logger.info("Testing database...")
    
    try:
        from database import PlanningDatabase
        
        # Initialize database
        db = PlanningDatabase(":memory:")  # Use in-memory database for testing
        
        # Test statistics (should be empty initially)
        stats = db.get_statistics()
        assert stats['total_applications'] == 0, "New database should have 0 applications"
        
        # Test inserting a sample application
        sample_app = {
            'project_id': 'TEST001',
            'borough': 'Test Borough',
            'title': 'Test application with noise monitoring',
            'address': '123 Test Street',
            'submission_date': '2024-01-01',
            'application_url': 'http://test.example.com',
            'detected_keywords': ['noise monitoring'],
            'source_url': 'http://test.search.com'
        }
        
        success = db.insert_planning_application(sample_app)
        assert success, "Failed to insert test application"
        
        # Test retrieving applications
        apps_df = db.get_applications()
        assert len(apps_df) == 1, "Should have 1 application after insert"
        
        logger.info("✅ Database tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_utils():
    """Test utility functions"""
    logger.info("Testing utilities...")
    
    try:
        from utils import TextProcessor, ValidationUtils, ScrapingUtils
        
        # Test text processing
        text = "  This is a test with   extra spaces  "
        cleaned = TextProcessor.clean_text(text)
        assert cleaned == "This is a test with extra spaces", f"Text cleaning failed: {cleaned}"
        
        # Test keyword detection
        text_with_keywords = "This project includes noise monitoring and dust monitoring systems"
        keywords = TextProcessor.detect_keywords(text_with_keywords)
        assert 'noise monitoring' in keywords, "Failed to detect 'noise monitoring'"
        assert 'dust monitoring' in keywords, "Failed to detect 'dust monitoring'"
        
        # Test date parsing
        date_str = "15/01/2024"
        parsed_date = TextProcessor.parse_date(date_str)
        assert parsed_date == "2024-01-15", f"Date parsing failed: {parsed_date}"
        
        # Test URL validation
        valid_url = "https://example.com/test"
        invalid_url = "not-a-url"
        assert ValidationUtils.is_valid_url(valid_url), "Valid URL not recognized"
        assert not ValidationUtils.is_valid_url(invalid_url), "Invalid URL not rejected"
        
        # Test project ID validation
        valid_id = "APP123456"
        invalid_id = ""
        assert ValidationUtils.is_valid_project_id(valid_id), "Valid project ID not recognized"
        assert not ValidationUtils.is_valid_project_id(invalid_id), "Invalid project ID not rejected"
        
        logger.info("✅ Utilities tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Utilities test failed: {e}")
        return False

def test_scrapers():
    """Test scraper creation"""
    logger.info("Testing scrapers...")
    
    try:
        from scrapers import create_scraper, IdoxScraper, SouthwarkScraper
        
        # Test scraper creation for each borough
        boroughs = ["Camden", "Westminster", "Hammersmith & Fulham", "Tower Hamlets", "Southwark"]
        
        for borough in boroughs:
            scraper = create_scraper(borough)
            assert scraper is not None, f"Failed to create scraper for {borough}"
            assert scraper.borough_name == borough, f"Borough name mismatch for {borough}"
            
            # Test that scrapers have required methods
            assert hasattr(scraper, 'scrape_applications'), f"Missing scrape_applications method for {borough}"
            assert hasattr(scraper, 'search_keyword'), f"Missing search_keyword method for {borough}"
        
        logger.info("✅ Scrapers tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Scrapers test failed: {e}")
        return False

def test_manager():
    """Test scraper manager"""
    logger.info("Testing scraper manager...")
    
    try:
        from scraper_manager import ScrapingManager
        
        # Initialize manager with test database
        manager = ScrapingManager(":memory:")
        
        # Test status retrieval
        status = manager.get_scraping_status()
        assert 'is_running' in status, "Missing is_running in status"
        assert 'boroughs' in status, "Missing boroughs in status"
        assert 'total_boroughs' in status, "Missing total_boroughs in status"
        
        logger.info("✅ Manager tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Manager test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    logger.info("🧪 Starting London Planning Application Monitor Tests")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Database", test_database),
        ("Utilities", test_utils),
        ("Scrapers", test_scrapers),
        ("Manager", test_manager)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            failed += 1
    
    # Summary
    logger.info(f"\n📊 Test Summary:")
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Application is ready to use.")
        return True
    else:
        logger.error("⚠️ Some tests failed. Please check the errors above.")
        return False

def main():
    """Main function"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n👋 Tests interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    main() 