#!/usr/bin/env python3
"""
Simple test script to try different approaches for accessing planning portals
"""

import requests
import time
from bs4 import BeautifulSoup
from config import BOROUGHS_CONFIG

def test_simple_get_requests():
    """Test simple GET requests to see what we can access"""
    print("🧪 TESTING SIMPLE GET REQUESTS")
    print("=" * 50)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    for borough, config in BOROUGHS_CONFIG.items():
        print(f"\n🏛️ Testing {borough}:")
        print(f"   Base URL: {config['base_url']}")
        
        try:
            # Test base URL
            response = session.get(config['base_url'], timeout=10)
            print(f"   ✅ Base URL: {response.status_code}")
            
            # Test search URL  
            time.sleep(2)
            search_response = session.get(config['search_url'], timeout=10)
            print(f"   📍 Search URL: {search_response.status_code}")
            
            if search_response.status_code == 200:
                # Try to parse the search page
                soup = BeautifulSoup(search_response.content, 'html.parser')
                
                # Look for forms
                forms = soup.find_all('form')
                print(f"   📝 Forms found: {len(forms)}")
                
                # Look for search inputs
                search_inputs = soup.find_all('input', {'name': lambda x: x and 'search' in x.lower()})
                proposal_inputs = soup.find_all('input', {'name': lambda x: x and 'proposal' in x.lower()})
                print(f"   🔍 Search inputs: {len(search_inputs)}")
                print(f"   📄 Proposal inputs: {len(proposal_inputs)}")
                
                # Look for any existing applications on the page
                links = soup.find_all('a', href=True)
                app_links = [link for link in links if any(term in link.get('href', '').lower() 
                           for term in ['application', 'planning', 'detail', 'view'])]
                print(f"   🔗 Application links: {len(app_links)}")
                
                if app_links:
                    print("   📋 Sample application links:")
                    for i, link in enumerate(app_links[:3]):
                        print(f"      {i+1}. {link.text.strip()[:50]}...")
                        
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}")

def test_alternative_urls():
    """Test alternative URLs that might work"""
    print("\n\n🔄 TESTING ALTERNATIVE ACCESS METHODS")
    print("=" * 50)
    
    # Try some common alternative paths
    alternative_paths = [
        '/applications',
        '/planning',
        '/search',
        '/public',
        '/online-applications',
        '/planning-applications'
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    
    for borough, config in BOROUGHS_CONFIG.items():
        print(f"\n🏛️ {borough} alternative paths:")
        base_url = config['base_url']
        
        for path in alternative_paths:
            try:
                url = base_url + path
                response = session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"   ✅ {path}: {response.status_code}")
                    
                    # Quick check for useful content
                    content = response.text.lower()
                    if any(term in content for term in ['application', 'planning', 'search']):
                        print(f"      🎯 Contains planning content!")
                        
            except:
                pass

def test_search_with_simple_terms():
    """Test searching with very simple terms that should have results"""
    print("\n\n🔍 TESTING SEARCH WITH SIMPLE TERMS")
    print("=" * 50)
    
    # Try very common terms that should return results
    test_terms = ['house', 'extension', 'garage', 'planning', 'application']
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    # Test Westminster as it's a common Idox system
    borough = "Westminster"
    config = BOROUGHS_CONFIG[borough]
    
    print(f"🏛️ Testing {borough} with simple search terms:")
    
    for term in test_terms:
        try:
            print(f"\n   🔍 Searching for: '{term}'")
            
            # Visit the search page first
            search_response = session.get(config['search_url'], timeout=10)
            print(f"   📄 Search page: {search_response.status_code}")
            
            if search_response.status_code == 200:
                time.sleep(2)  # Be polite
                
                # Try a simple POST with minimal data
                search_data = {
                    'searchCriteria.proposal': term,
                    'searchType': 'Application',
                    'action': 'search'
                }
                
                post_response = session.post(
                    config['search_url'], 
                    data=search_data,
                    timeout=15,
                    allow_redirects=True
                )
                
                print(f"   📊 Search result: {post_response.status_code}")
                
                if post_response.status_code == 200:
                    # Check if we got results
                    soup = BeautifulSoup(post_response.content, 'html.parser')
                    
                    # Look for result indicators
                    result_table = soup.find('table', {'class': 'searchresults'})
                    result_rows = soup.find_all('tr') if result_table else []
                    
                    print(f"   📋 Result rows found: {len(result_rows)}")
                    
                    if len(result_rows) > 1:  # More than just header
                        print(f"   🎉 SUCCESS! Found results for '{term}'")
                        
                        # Show first few results
                        for i, row in enumerate(result_rows[1:4]):  # Skip header, show first 3
                            cells = row.find_all('td')
                            if cells:
                                app_info = cells[0].text.strip()[:30]
                                print(f"      {i+1}. {app_info}...")
                                
                        return True  # Found working search!
                        
                elif post_response.status_code == 403:
                    print(f"   🚫 Blocked (403) - Anti-bot protection active")
                else:
                    print(f"   ⚠️ Unexpected status: {post_response.status_code}")
                    
        except Exception as e:
            print(f"   ❌ Error with '{term}': {str(e)[:40]}")
            
        time.sleep(3)  # Wait between searches

if __name__ == "__main__":
    print("🚀 PLANNING PORTAL SIMPLE TESTING")
    print("This will test different approaches to access planning data")
    print("=" * 80)
    
    # Test 1: Simple GET requests
    test_simple_get_requests()
    
    # Test 2: Alternative URLs
    test_alternative_urls()
    
    # Test 3: Simple search terms
    test_search_with_simple_terms()
    
    print("\n\n🎯 TESTING COMPLETE")
    print("Check the output above to see which approaches work!") 