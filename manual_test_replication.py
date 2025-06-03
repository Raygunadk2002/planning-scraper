#!/usr/bin/env python3
"""
Replicate the manual browser success with more specific search criteria
"""

import requests
from bs4 import BeautifulSoup
import time

def test_specific_searches():
    """Test specific searches that should return manageable results"""
    
    print("🎉 MANUAL SUCCESS REPLICATION TEST")
    print("Testing more specific searches based on manual browser success")
    print("=" * 80)
    
    base_url = "https://idoxpa.westminster.gov.uk"
    search_url = f"{base_url}/online-applications/search.do?action=simple&searchType=Application"
    
    # More specific search terms to avoid "too many results"
    specific_searches = [
        "single storey extension",
        "two storey extension", 
        "rear extension",
        "side extension",
        "house extension",
        "loft extension",
        "basement extension",
        "conservatory extension"
    ]
    
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
    
    for search_term in specific_searches:
        print(f"\n🔍 Testing: '{search_term}'")
        print("-" * 50)
        
        try:
            # Get search page first
            response = session.get(search_url)
            if response.status_code != 200:
                print(f"   ❌ Can't access search page: {response.status_code}")
                continue
                
            print(f"   ✅ Search page loaded: {response.status_code}")
            
            # Parse form to get correct field names
            soup = BeautifulSoup(response.content, 'html.parser')
            form = soup.find('form')
            
            if not form:
                print("   ❌ No form found")
                continue
                
            # Build form data
            form_data = {}
            
            # Look for common field names
            proposal_fields = ['proposal', 'description', 'caseDescription', 'details']
            for field_name in proposal_fields:
                field = soup.find('input', {'name': field_name}) or soup.find('textarea', {'name': field_name})
                if field:
                    form_data[field_name] = search_term
                    print(f"   📝 Using field: {field_name}")
                    break
                    
            if not form_data:
                print("   ❌ No proposal field found")
                continue
            
            # Add other common form fields
            hidden_fields = soup.find_all('input', {'type': 'hidden'})
            for field in hidden_fields:
                name = field.get('name')
                value = field.get('value')
                if name and value:
                    form_data[name] = value
            
            # Add submit action
            form_data['submit'] = 'Search'
            
            print(f"   📤 Submitting form with {len(form_data)} fields")
            
            # Submit search
            search_response = session.post(search_url, data=form_data, timeout=15)
            
            print(f"   📊 Response: {search_response.status_code}")
            
            if search_response.status_code == 200:
                content = search_response.text.lower()
                
                if "too many results" in content:
                    print("   ⚠️ Too many results (success but need refinement)")
                elif "no results" in content or "no applications found" in content:
                    print("   📭 No results found")
                elif "application" in content and "reference" in content:
                    print("   🎉 RESULTS FOUND! Parsing...")
                    
                    # Try to parse results
                    results_soup = BeautifulSoup(search_response.content, 'html.parser')
                    tables = results_soup.find_all('table')
                    
                    for table in tables:
                        rows = table.find_all('tr')
                        if len(rows) > 1:  # Has data rows
                            print(f"      📋 Found table with {len(rows)-1} rows")
                            
                            # Show first few results
                            for i, row in enumerate(rows[1:3], 1):  # First 2 data rows
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 2:
                                    ref = cells[0].get_text(strip=True)
                                    desc = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                                    print(f"      {i}. {ref}: {desc[:50]}...")
                else:
                    print("   ❓ Unknown response format")
                    
            elif search_response.status_code == 403:
                print("   🚫 Still blocked (403) - automated request detected")
            else:
                print(f"   ❌ Error: {search_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:50]}")
            
        time.sleep(2)  # Be polite
    
    print("\n\n🎯 SUMMARY")
    print("=" * 40)
    print("Manual browser search works but automated requests may still be blocked")
    print("Next step: Use Selenium to perfectly mimic human behavior")

if __name__ == "__main__":
    test_specific_searches() 