#!/usr/bin/env python3
"""
Quick status check for all scrapers
"""

from scraper_manager import ScrapingManager
import json

def main():
    print('🎯 COMPLETE SYSTEM STATUS REPORT')
    print('=' * 80)

    # Initialize the scraping manager
    manager = ScrapingManager()

    # Get detailed status
    status = manager.get_scraping_status()
    print(json.dumps(status, indent=2))

    print('\n🚀 QUICK SCRAPER TEST')
    print('=' * 40)

    # Try to run a quick scrape on Westminster
    for borough in ['Westminster']:
        print(f'\n🏛️ Testing {borough}:')
        try:
            scraper = manager.scrapers[borough]
            print(f'   ✅ Scraper available: {type(scraper).__name__}')
            print(f'   🌐 Base URL: {scraper.base_url}')
            print(f'   🔍 Search URL: {scraper.search_url}')
            
            # Try a minimal search
            results = scraper.search_applications(['test'])
            print(f'   📊 Search completed with {len(results)} results')
            
        except Exception as e:
            print(f'   ❌ Error: {str(e)[:60]}')

    print('\n✅ Status check complete!')
    print('\n🎉 NEXT STEPS:')
    print('1. Try manual browser test on Westminster')
    print('2. Check Streamlit dashboard: http://localhost:8502')
    print('3. Wait for Chrome/ChromeDriver version sync')
    print('4. Re-run selenium_bypass.py')

if __name__ == "__main__":
    main() 