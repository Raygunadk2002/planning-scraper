#!/usr/bin/env python3
"""
Get actual planning applications using more specific search terms
"""

import requests
from bs4 import BeautifulSoup
import time
import re

def get_westminster_applications():
    print("🎯 GETTING ACTUAL PLANNING APPLICATIONS")
    print("Using more specific search terms")
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
    
    # More specific search terms (less likely to return "too many results")
    specific_terms = [
        "basement extension monitoring",
        "noise monitoring extension", 
        "vibration monitoring",
        "dust monitoring construction",
        "environmental monitoring basement",
        "subsidence monitoring",
        "monitoring during construction",
        "construction monitoring plan",
        "rear extension vibration",
        "loft conversion monitoring"
    ]
    
    all_applications = []
    
    for search_term in specific_terms:
        print(f"\n🔍 Testing: '{search_term}'")
        print("-" * 50)
        
        try:
            # Get search page and CSRF token
            response = session.get(search_url)
            if response.status_code != 200:
                print(f"   ❌ Can't access search page: {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            csrf_input = soup.find('input', {'name': '_csrf'})
            if not csrf_input:
                print("   ❌ No CSRF token found")
                continue
                
            csrf_token = csrf_input.get('value')
            
            # Build form data
            form_data = {
                '_csrf': csrf_token,
                'searchType': 'Application',
                'searchCriteria.caseStatus': '',
                'searchCriteria.simpleSearchString': search_term,
                'searchCriteria.simpleSearch': 'true'
            }
            
            # Set referer and submit
            session.headers['Referer'] = search_url
            search_response = session.post(submit_url, data=form_data, timeout=15)
            
            print(f"   📊 Response: {search_response.status_code}")
            
            if search_response.status_code == 200:
                content = search_response.text.lower()
                
                if "too many results found" in content:
                    print("   ⚠️ Still too many results - trying next term")
                    
                elif "no results" in content or "no applications found" in content:
                    print("   📭 No results found")
                    
                elif "application" in content:
                    print("   🎉 SUCCESS! Applications found!")
                    
                    # Parse the results
                    results_soup = BeautifulSoup(search_response.content, 'html.parser')
                    applications = parse_applications(results_soup, search_term)
                    
                    if applications:
                        all_applications.extend(applications)
                        print(f"   📋 Found {len(applications)} applications")
                        
                        # Show first few
                        for i, app in enumerate(applications[:3], 1):
                            print(f"      {i}. {app['reference']}: {app['description'][:50]}...")
                            
                        # If we found results with monitoring keywords, we're done!
                        monitoring_apps = [app for app in applications if has_monitoring_keywords(app)]
                        if monitoring_apps:
                            print(f"   🎯 {len(monitoring_apps)} applications with monitoring keywords!")
                            return all_applications
                    else:
                        print("   ❓ Applications found but couldn't parse")
                        
                else:
                    print("   ❓ Unknown response format")
                    
            elif search_response.status_code == 403:
                print("   🚫 Blocked (403)")
                
            else:
                print(f"   ❌ Error: {search_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:50]}")
            
        time.sleep(2)  # Be polite
    
    return all_applications

def parse_applications(soup, search_term):
    """Parse applications from search results"""
    applications = []
    
    try:
        # Look for results table
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            
            if len(rows) < 2:  # Need header + data
                continue
                
            # Check if this looks like a results table
            header_row = rows[0]
            header_text = header_row.get_text().lower()
            
            if 'application' not in header_text and 'reference' not in header_text:
                continue
                
            # Parse data rows
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 3:  # Need at least ref, address, description
                    continue
                    
                try:
                    # Extract application data
                    ref_cell = cells[0]
                    ref_link = ref_cell.find('a')
                    
                    if ref_link:
                        app_ref = ref_link.get_text(strip=True)
                        app_url = ref_link.get('href', '')
                        
                        # Make full URL
                        if app_url and not app_url.startswith('http'):
                            app_url = f"https://idoxpa.westminster.gov.uk{app_url}"
                    else:
                        app_ref = ref_cell.get_text(strip=True)
                        app_url = ""
                    
                    # Get other details
                    address = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    description = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    status = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    
                    # Validate application reference format
                    if not re.search(r'[0-9]{4,}', app_ref):
                        continue
                        
                    application = {
                        'reference': app_ref,
                        'address': address,
                        'description': description,
                        'status': status,
                        'url': app_url,
                        'search_term': search_term,
                        'borough': 'Westminster'
                    }
                    
                    applications.append(application)
                    
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"      ❌ Parse error: {str(e)[:30]}")
        
    return applications

def has_monitoring_keywords(application):
    """Check if application contains monitoring keywords"""
    monitoring_keywords = [
        'monitoring', 'noise', 'vibration', 'dust', 'subsidence',
        'environmental', 'acoustic', 'sound', 'construction management'
    ]
    
    text_to_search = f"{application['description']} {application['address']}".lower()
    
    for keyword in monitoring_keywords:
        if keyword in text_to_search:
            return True
            
    return False

if __name__ == "__main__":
    applications = get_westminster_applications()
    
    print("\n\n🎯 FINAL RESULTS")
    print("=" * 80)
    
    if applications:
        print(f"📊 Total applications found: {len(applications)}")
        
        # Filter for monitoring keywords
        monitoring_apps = [app for app in applications if has_monitoring_keywords(app)]
        
        if monitoring_apps:
            print(f"🎉 {len(monitoring_apps)} applications with monitoring keywords:")
            
            for i, app in enumerate(monitoring_apps, 1):
                print(f"\n{i}. 📋 {app['reference']}")
                print(f"   Address: {app['address']}")
                print(f"   Description: {app['description']}")
                print(f"   Status: {app['status']}")
                print(f"   URL: {app['url']}")
                print(f"   Found via: {app['search_term']}")
        else:
            print("📋 No applications with specific monitoring keywords found")
            print("But found applications - try broader search terms")
    else:
        print("❌ No applications found")
        print("All searches returned 'too many results' or 'no results'")
        print("Try manual browser with more specific terms") 