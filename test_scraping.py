#!/usr/bin/env python3
"""
Test script to run scrapers and see what they're finding
"""

import sys
import time
import requests
from scraper_manager import ScrapingManager

def test_url_accessibility():
    """Test if the planning portals are accessible"""
    print("=== TESTING URL ACCESSIBILITY ===\n")
    
    from config import BOROUGHS_CONFIG, SCRAPING_CONFIG
    
    headers = {
        'User-Agent': SCRAPING_CONFIG['user_agent'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    for borough_name, config in BOROUGHS_CONFIG.items():
        print(f"🌐 Testing {borough_name}...")
        base_url = config['base_url']
        
        try:
            response = requests.get(base_url, headers=headers, timeout=10)
            print(f"   Base URL: {base_url}")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Accessible")
            elif response.status_code == 403:
                print("   🚫 Blocked (403 Forbidden) - Anti-bot protection")
            elif response.status_code == 404:
                print("   ❌ Not Found (404) - URL may be outdated")
            else:
                print(f"   ⚠️ Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

def test_scraping():
    print("=== TESTING SCRAPER OUTPUTS ===\n")
    
    # First test URL accessibility
    test_url_accessibility()
    
    # Create manager
    print("🔧 Creating ScrapingManager...")
    manager = ScrapingManager()
    
    print(f"✅ Manager created with {len(manager.scrapers)} scrapers\n")
    
    # Test a single borough first
    test_borough = "Westminster"  # Changed from Camden to Westminster
    
    print(f"🎯 Testing {test_borough} scraper...")
    print(f"📍 Target URL: {manager.scrapers[test_borough].config['search_url']}")
    print("⏰ Starting scrape with simple search term...\n")
    
    start_time = time.time()
    # Use a simpler search term that's more likely to have results
    result = manager.scrape_single_borough(test_borough, keywords=["extension"])
    end_time = time.time()
    
    print(f"\n⏱️ Scraping completed in {end_time - start_time:.1f} seconds")
    print(f"📊 Result: {result}")
    
    if result.get('success'):
        total_found = result.get('total_found', 0)
        new_apps = result.get('new_applications', 0)
        
        print(f"\n✅ SUCCESS!")
        print(f"   📈 Total applications found: {total_found}")
        print(f"   🆕 New applications: {new_apps}")
        print(f"   🔍 Keywords searched: {result.get('keywords_searched', 0)}")
        print(f"   🌐 HTTP requests made: {result.get('requests_made', 0)}")
        print(f"   📄 Pages processed: {result.get('pages_processed', 0)}")
        
        if total_found > 0:
            print(f"\n🎉 GREAT! The scraper IS finding planning applications!")
            print(f"   This means the portals are accessible and working.")
        else:
            print(f"\n⚠️ No applications found for 'extension' keyword.")
            print(f"   This could mean:")
            print(f"   - No current applications match this keyword")
            print(f"   - The portal structure has changed")
            print(f"   - Network/access issues")
    else:
        print(f"\n❌ FAILED: {result.get('error')}")
    
    # Show recent activity
    status = manager.get_scraping_status()
    recent_activity = status.get('live_activity', [])
    
    if recent_activity:
        print(f"\n📋 RECENT ACTIVITY LOG (last 10 entries):")
        for entry in recent_activity[-10:]:
            timestamp = entry['timestamp']
            borough = entry['borough'] or 'SYSTEM'
            message = entry['message']
            print(f"   [{timestamp}] {borough}: {message}")
    
    print(f"\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    test_scraping() 