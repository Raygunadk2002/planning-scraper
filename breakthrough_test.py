#!/usr/bin/env python3
"""
BREAKTHROUGH TEST - Using the correct Westminster form field
Based on manual browser success: "Too many results found"
"""

import requests
from bs4 import BeautifulSoup
import time

def test_westminster_breakthrough():
    print("🎉 WESTMINSTER BREAKTHROUGH TEST")
    print("Using discovered form field: searchCriteria.simpleSearchString")
    print("=" * 80)
    
    base_url = "https://idoxpa.westminster.gov.uk"
    search_url = f"{base_url}/online-applications/search.do"
    submit_url = f"{base_url}/online-applications/simpleSearchResults.do?action=firstPage"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin'
    })
    
    # Test different search terms
    search_terms = [
        "extension",  # Same as manual test
        "rear extension",
        "single storey extension", 
        "house extension",
        "basement extension"
    ]
    
    for search_term in search_terms:
        print(f"\n🔍 Testing: '{search_term}'")
        print("-" * 50)
        
        try:
            # First, get the search page to extract CSRF token
            print("   📄 Getting search page...")
            response = session.get(search_url)
            
            if response.status_code != 200:
                print(f"   ❌ Can't access search page: {response.status_code}")
                continue
                
            # Parse to get CSRF token
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf'})
            
            if not csrf_input:
                print("   ❌ No CSRF token found")
                continue
                
            csrf_token = csrf_input.get('value')
            print(f"   🔑 CSRF token: {csrf_token[:20]}...")
            
            # Build form data exactly like the real form
            form_data = {
                '_csrf': csrf_token,
                'searchType': 'Application',
                'searchCriteria.caseStatus': '',  # All statuses
                'searchCriteria.simpleSearchString': search_term,
                'searchCriteria.simpleSearch': 'true'
            }
            
            print(f"   📤 Submitting to: {submit_url}")
            print(f"   📝 Form data: {len(form_data)} fields")
            
            # Set referer
            session.headers['Referer'] = search_url
            
            # Submit the search
            search_response = session.post(submit_url, data=form_data, timeout=15)
            
            print(f"   📊 Response: {search_response.status_code}")
            
            if search_response.status_code == 200:
                content = search_response.text.lower()
                
                if "too many results found" in content or "too many results" in content:
                    print("   🎉 SUCCESS! Too many results found (exactly like manual test!)")
                    print("   ✅ BREAKTHROUGH CONFIRMED!")
                    
                    # Try to count results
                    if "please enter some more parameters" in content:
                        print("   📋 Response: 'Please enter some more parameters'")
                        
                    return True
                    
                elif "no results" in content or "no applications found" in content:
                    print("   📭 No results found for this term")
                    
                elif "forbidden" in content or "access denied" in content:
                    print("   🚫 Access denied - still blocked")
                    
                elif "application" in content and ("reference" in content or "ref" in content):
                    print("   🎉 SUCCESS! Results found and parsed!")
                    
                    # Try to parse actual results
                    results_soup = BeautifulSoup(search_response.content, 'html.parser')
                    tables = results_soup.find_all('table')
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 1:  # Has data
                            print(f"      📋 Found results table with {len(rows)-1} applications")
                            
                            # Show first few
                            for i, row in enumerate(rows[1:3], 1):
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    ref = cells[0].get_text(strip=True)
                                    desc = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                    print(f"      {i}. {ref}: {desc[:50]}...")
                                    
                    return True
                    
                else:
                    print("   ❓ Unknown response format")
                    # Save snippet for analysis
                    snippet = content[:200].replace('\n', ' ')
                    print(f"   📄 Content preview: {snippet}...")
                    
            elif search_response.status_code == 403:
                print("   🚫 Still blocked (403) - automated request detected")
                
            elif search_response.status_code == 500:
                print("   ⚠️ Server error (500) - may be temporary")
                
            else:
                print(f"   ❌ Unexpected response: {search_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:50]}")
            
        time.sleep(3)  # Be polite between searches
    
    print("\n\n🎯 SUMMARY")
    print("=" * 40)
    print("If no success above, the protection is sophisticated")
    print("Next step: Selenium human-behavior bypass")
    
    return False

if __name__ == "__main__":
    success = test_westminster_breakthrough()
    
    if success:
        print("\n🚀 READY FOR PRODUCTION!")
        print("We can now automate the successful manual approach")
    else:
        print("\n🤖 SELENIUM REQUIRED")
        print("Need human-like behavior to bypass advanced protection") 